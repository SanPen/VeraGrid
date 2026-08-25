# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np
import numpy.typing as npt
import scipy.interpolate as interpolate
import scipy.linalg as la
import scipy.optimize as optimize
import scipy.signal as signal
import scipy.sparse.linalg as spla
from numpy.lib.stride_tricks import sliding_window_view

from VeraGridEngine.basic_structures import CxMat, CxVec, IntVec, Mat, Vec
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_options import (
    EraMatrixPencilBand,
    EraMatrixPencilOptions,
    create_default_era_analysis_bands,
)
from VeraGridEngine.Simulations.SmallSignalStabilityEmt.era_matrix_pencil_results import (
    EraMatrixPencilResults,
)


class EraChannelScaling:
    """
    Container for channel centering and scaling information.

    The object is immutable after construction because residue rescaling must
    use the exact same channel statistics that were used to normalize the data.
    """

    __slots__ = (
        '_means',
        '_scales',
    )

    def __init__(self, means: Vec, scales: Vec) -> None:
        """
        Store channel centering and scaling arrays.

        :param means: Per-channel means.
        :param scales: Per-channel standard deviations or robust scale factors.
        :return: None.
        """
        self._means: Vec = np.asarray(means, dtype=np.float64)
        self._scales: Vec = np.asarray(scales, dtype=np.float64)

    def get_means(self) -> Vec:
        """
        Return the per-channel means.

        :return: Mean vector.
        """
        return self._means

    def get_scales(self) -> Vec:
        """
        Return the per-channel scaling vector.

        :return: Scaling vector.
        """
        return self._scales


class EraBandSignal:
    """
    Prepared sub-band signal and its numerical metadata.

    The class holds all information required to solve one band independently so
    the outer driver can later parallelize bands without shared mutable state.
    """

    __slots__ = (
        '_time_data',
        '_signal_data',
        '_physical_scales',
        '_time_step',
        '_sampling_frequency_hz',
        '_low_hz',
        '_high_hz',
        '_decimation_factor',
    )

    def __init__(self,
                 time_data: Vec,
                 signal_data: Mat,
                 physical_scales: Vec,
                 time_step: float,
                 sampling_frequency_hz: float,
                 low_hz: float,
                 high_hz: float,
                 decimation_factor: int) -> None:
        """
        Store one prepared sub-band record.

        :param time_data: Time vector of the decimated band.
        :param signal_data: Standardized band-limited observation matrix.
        :param physical_scales: Original per-channel scaling factors.
        :param time_step: Effective decimated time step.
        :param sampling_frequency_hz: Effective sampling frequency.
        :param low_hz: Lower band edge.
        :param high_hz: Upper band edge.
        :param decimation_factor: Effective integer decimation factor.
        :return: None.
        """
        self._time_data: Vec = np.asarray(time_data, dtype=np.float64)
        self._signal_data: Mat = np.asarray(signal_data, dtype=np.float64)
        self._physical_scales: Vec = np.asarray(physical_scales, dtype=np.float64)
        self._time_step: float = float(time_step)
        self._sampling_frequency_hz: float = float(sampling_frequency_hz)
        self._low_hz: float = float(low_hz)
        self._high_hz: float = float(high_hz)
        self._decimation_factor: int = int(decimation_factor)

    def get_time_data(self) -> Vec:
        """
        Return the decimated time vector.

        :return: Time vector.
        """
        return self._time_data

    def get_signal_data(self) -> Mat:
        """
        Return the standardized band-limited observation matrix.

        :return: Observation matrix.
        """
        return self._signal_data

    def get_physical_scales(self) -> Vec:
        """
        Return the original per-channel scaling factors.

        :return: Scaling vector.
        """
        return self._physical_scales

    def get_time_step(self) -> float:
        """
        Return the effective decimated time step.

        :return: Time step in seconds.
        """
        return self._time_step

    def get_sampling_frequency_hz(self) -> float:
        """
        Return the effective decimated sampling frequency.

        :return: Sampling frequency in Hz.
        """
        return self._sampling_frequency_hz

    def get_low_hz(self) -> float:
        """
        Return the lower band edge.

        :return: Frequency in Hz.
        """
        return self._low_hz

    def get_high_hz(self) -> float:
        """
        Return the upper band edge.

        :return: Frequency in Hz.
        """
        return self._high_hz

    def get_decimation_factor(self) -> int:
        """
        Return the effective integer decimation factor.

        :return: Positive decimation factor.
        """
        return self._decimation_factor


class EraSvdDecomposition:
    """
    SVD decomposition used by the TLS matrix pencil stage.

    The object keeps the right singular vectors because the shift-invariant TLS
    generalized eigenproblem is constructed from the right subspace.
    """

    __slots__ = (
        '_singular_values',
        '_right_vectors',
        '_condition_number',
        '_truncated_backend',
    )

    def __init__(self,
                 singular_values: Vec,
                 right_vectors: CxMat,
                 condition_number: float,
                 truncated_backend: bool) -> None:
        """
        Store one SVD decomposition.

        :param singular_values: Singular-value vector.
        :param right_vectors: Right singular vectors as columns.
        :param condition_number: Estimated condition number.
        :param truncated_backend: Flag indicating a truncated backend.
        :return: None.
        """
        self._singular_values: Vec = np.asarray(singular_values, dtype=np.float64)
        self._right_vectors: CxMat = np.asarray(right_vectors, dtype=np.complex128)
        self._condition_number: float = float(condition_number)
        self._truncated_backend: bool = bool(truncated_backend)

    def get_singular_values(self) -> Vec:
        """
        Return the singular values.

        :return: Singular-value vector.
        """
        return self._singular_values

    def get_right_vectors(self) -> CxMat:
        """
        Return the right singular vectors.

        :return: Matrix whose columns are right singular vectors.
        """
        return self._right_vectors

    def get_condition_number(self) -> float:
        """
        Return the condition-number estimate.

        :return: Condition-number estimate.
        """
        return self._condition_number

    def get_truncated_backend(self) -> bool:
        """
        Return whether the decomposition came from a truncated backend.

        :return: ``True`` when the decomposition is truncated.
        """
        return self._truncated_backend


class EraBandResult:
    """
    Result of one independent band extraction.

    The object only stores one band outcome, which is the required shape for a
    later multiprocessing or joblib-style parallel map.
    """

    __slots__ = (
        '_poles_s',
        '_poles_z',
        '_residues',
        '_modal_energy',
        '_reconstruction_error',
        '_band_low_hz',
        '_band_high_hz',
        '_selected_order',
        '_observable_count',
        '_condition_number',
        '_successful',
    )

    def __init__(self,
                 poles_s: CxVec,
                 poles_z: CxVec,
                 residues: CxMat,
                 modal_energy: Vec,
                 reconstruction_error: float,
                 band_low_hz: float,
                 band_high_hz: float,
                 selected_order: int,
                 observable_count: int,
                 condition_number: float,
                 successful: bool) -> None:
        """
        Store one band-extraction result.

        :param poles_s: Continuous-time poles.
        :param poles_z: Discrete-time poles.
        :param residues: Physical residue matrix.
        :param modal_energy: Relative modal-energy vector.
        :param reconstruction_error: Global reconstruction error for the band.
        :param band_low_hz: Lower edge of the source band.
        :param band_high_hz: Upper edge of the source band.
        :param selected_order: Effective subspace order.
        :param observable_count: Number of channels used in the band.
        :param condition_number: Condition-number estimate.
        :param successful: ``True`` when the band produced valid modes.
        :return: None.
        """
        self._poles_s: CxVec = np.asarray(poles_s, dtype=np.complex128)
        self._poles_z: CxVec = np.asarray(poles_z, dtype=np.complex128)
        self._residues: CxMat = np.asarray(residues, dtype=np.complex128)
        self._modal_energy: Vec = np.asarray(modal_energy, dtype=np.float64)
        self._reconstruction_error: float = float(reconstruction_error)
        self._band_low_hz: float = float(band_low_hz)
        self._band_high_hz: float = float(band_high_hz)
        self._selected_order: int = int(selected_order)
        self._observable_count: int = int(observable_count)
        self._condition_number: float = float(condition_number)
        self._successful: bool = bool(successful)

    def get_poles_s(self) -> CxVec:
        """
        Return the continuous-time poles.

        :return: Complex pole vector.
        """
        return self._poles_s

    def get_poles_z(self) -> CxVec:
        """
        Return the discrete-time poles.

        :return: Complex pole vector.
        """
        return self._poles_z

    def get_residues(self) -> CxMat:
        """
        Return the physical residue matrix.

        :return: Complex residue matrix.
        """
        return self._residues

    def get_modal_energy(self) -> Vec:
        """
        Return the relative modal-energy vector.

        :return: Modal-energy vector.
        """
        return self._modal_energy

    def get_reconstruction_error(self) -> float:
        """
        Return the global reconstruction error.

        :return: Relative reconstruction error.
        """
        return self._reconstruction_error

    def get_band_low_hz(self) -> float:
        """
        Return the lower source-band edge.

        :return: Frequency in Hz.
        """
        return self._band_low_hz

    def get_band_high_hz(self) -> float:
        """
        Return the upper source-band edge.

        :return: Frequency in Hz.
        """
        return self._band_high_hz

    def get_selected_order(self) -> int:
        """
        Return the selected subspace order.

        :return: Integer order.
        """
        return self._selected_order

    def get_observable_count(self) -> int:
        """
        Return how many channels participated in this band extraction.

        :return: Number of observables.
        """
        return self._observable_count

    def get_condition_number(self) -> float:
        """
        Return the band condition-number estimate.

        :return: Condition-number estimate.
        """
        return self._condition_number

    def get_successful(self) -> bool:
        """
        Return whether the band produced valid modes.

        :return: Success flag.
        """
        return self._successful


class EraMergedModalData:
    """
    Fused modal data produced after multi-band clustering.

    The class feeds the final public result container while keeping all
    intermediate fusion logic detached from the GUI-facing object.
    """

    __slots__ = (
        '_poles_s',
        '_residues',
        '_modal_energy',
        '_reconstruction_errors',
        '_band_low_hz',
        '_band_high_hz',
        '_selected_orders',
        '_observable_count_per_mode',
    )

    def __init__(self,
                 poles_s: CxVec,
                 residues: CxMat,
                 modal_energy: Vec,
                 reconstruction_errors: Vec,
                 band_low_hz: Vec,
                 band_high_hz: Vec,
                 selected_orders: IntVec,
                 observable_count_per_mode: IntVec) -> None:
        """
        Store fused modal data.

        :param poles_s: Fused continuous-time poles.
        :param residues: Fused physical residues.
        :param modal_energy: Fused modal-energy vector.
        :param reconstruction_errors: Reconstruction-error vector.
        :param band_low_hz: Lower source-band vector.
        :param band_high_hz: Upper source-band vector.
        :param selected_orders: Selected-order vector.
        :param observable_count_per_mode: Observable-count vector.
        :return: None.
        """
        self._poles_s: CxVec = np.asarray(poles_s, dtype=np.complex128)
        self._residues: CxMat = np.asarray(residues, dtype=np.complex128)
        self._modal_energy: Vec = np.asarray(modal_energy, dtype=np.float64)
        self._reconstruction_errors: Vec = np.asarray(reconstruction_errors, dtype=np.float64)
        self._band_low_hz: Vec = np.asarray(band_low_hz, dtype=np.float64)
        self._band_high_hz: Vec = np.asarray(band_high_hz, dtype=np.float64)
        self._selected_orders: IntVec = np.asarray(selected_orders, dtype=np.int_)
        self._observable_count_per_mode: IntVec = np.asarray(observable_count_per_mode, dtype=np.int_)

    def get_poles_s(self) -> CxVec:
        """
        Return the fused continuous-time poles.

        :return: Complex pole vector.
        """
        return self._poles_s

    def get_residues(self) -> CxMat:
        """
        Return the fused physical residues.

        :return: Complex residue matrix.
        """
        return self._residues

    def get_modal_energy(self) -> Vec:
        """
        Return the fused modal-energy vector.

        :return: Modal-energy vector.
        """
        return self._modal_energy

    def get_reconstruction_errors(self) -> Vec:
        """
        Return the reconstruction-error vector.

        :return: Reconstruction-error vector.
        """
        return self._reconstruction_errors

    def get_band_low_hz(self) -> Vec:
        """
        Return the lower source-band vector.

        :return: Lower-band vector.
        """
        return self._band_low_hz

    def get_band_high_hz(self) -> Vec:
        """
        Return the upper source-band vector.

        :return: Upper-band vector.
        """
        return self._band_high_hz

    def get_selected_orders(self) -> IntVec:
        """
        Return the selected-order vector.

        :return: Integer vector of orders.
        """
        return self._selected_orders

    def get_observable_count_per_mode(self) -> IntVec:
        """
        Return the per-mode observable-count vector.

        :return: Integer vector of observable counts.
        """
        return self._observable_count_per_mode


def build_empty_complex_vector() -> CxVec:
    """
    Build one empty complex vector.

    :return: Empty complex vector.
    """
    return np.zeros(0, dtype=np.complex128)


def build_empty_float_vector() -> Vec:
    """
    Build one empty real vector.

    :return: Empty real vector.
    """
    return np.zeros(0, dtype=np.float64)


def build_empty_complex_matrix() -> CxMat:
    """
    Build one empty complex matrix.

    :return: Empty complex matrix.
    """
    return np.zeros((0, 0), dtype=np.complex128)


def create_empty_band_result(observable_count: int, low_hz: float, high_hz: float) -> EraBandResult:
    """
    Build an empty band result.

    :param observable_count: Number of observables assigned to the band.
    :param low_hz: Lower source-band edge.
    :param high_hz: Upper source-band edge.
    :return: Empty unsuccessful band result.
    """
    return EraBandResult(
        poles_s=build_empty_complex_vector(),
        poles_z=build_empty_complex_vector(),
        residues=build_empty_complex_matrix(),
        modal_energy=build_empty_float_vector(),
        reconstruction_error=1.0,
        band_low_hz=low_hz,
        band_high_hz=high_hz,
        selected_order=0,
        observable_count=observable_count,
        condition_number=np.inf,
        successful=False,
    )


def create_empty_merged_modal_data() -> EraMergedModalData:
    """
    Build one empty fused modal container.

    :return: Empty merged modal data.
    """
    return EraMergedModalData(
        poles_s=build_empty_complex_vector(),
        residues=build_empty_complex_matrix(),
        modal_energy=build_empty_float_vector(),
        reconstruction_errors=build_empty_float_vector(),
        band_low_hz=build_empty_float_vector(),
        band_high_hz=build_empty_float_vector(),
        selected_orders=np.zeros(0, dtype=np.int_),
        observable_count_per_mode=np.zeros(0, dtype=np.int_),
    )


def evaluate_exponential_offset_model(time_data: Vec,
                                      offset: float,
                                      amplitude: float,
                                      decay_rate: float) -> Vec:
    """
    Evaluate the exponential DC-offset model used during detrending.

    :param time_data: Time vector.
    :param offset: Constant offset term.
    :param amplitude: Exponential amplitude term.
    :param decay_rate: Positive decay rate.
    :return: Model vector.
    """
    return offset + amplitude * np.exp(-decay_rate * time_data)


def convert_signal_to_2d(y_data: np.ndarray) -> Mat:
    """
    Ensure that the input observation array is two-dimensional.

    :param y_data: Raw observation array.
    :return: Two-dimensional observation matrix.
    """
    if y_data.ndim == 1:
        signal_2d: Mat = np.asarray(y_data.reshape(-1, 1), dtype=np.float64)
    else:
        signal_2d = np.asarray(y_data, dtype=np.float64)

    return signal_2d


def infer_uniform_time_step(time_data: Vec, fallback_step: float) -> float:
    """
    Infer the effective uniform time step from a possibly adaptive time grid.

    :param time_data: Time vector.
    :param fallback_step: Fallback value when the estimate is impossible.
    :return: Effective time step.
    """
    n_samples: int = int(time_data.shape[0])

    if n_samples >= 2:
        raw_differences: Vec = np.diff(time_data).astype(np.float64)
        positive_differences: Vec = raw_differences[raw_differences > 0.0]

        if positive_differences.shape[0] > 0:
            inferred_step: float = float(np.median(positive_differences))
        else:
            inferred_step = float(fallback_step)
    else:
        inferred_step = float(fallback_step)

    if inferred_step > 0.0:
        return inferred_step
    else:
        return max(float(fallback_step), 1e-6)


def resample_to_uniform_time_grid(time_data: Vec,
                                  y_data: Mat,
                                  target_step: float) -> Tuple[Vec, Mat]:
    """
    Resample the observations onto a uniform time grid.

    :param time_data: Original time vector.
    :param y_data: Observation matrix.
    :param target_step: Requested uniform time step.
    :return: Tuple ``(uniform_time, uniform_signal)``.
    """
    n_samples: int = int(time_data.shape[0])
    n_channels: int = int(y_data.shape[1])

    if n_samples >= 2 and target_step > 0.0:
        duration: float = float(time_data[-1] - time_data[0])
        target_count: int = int(np.floor(duration / target_step)) + 1

        if target_count >= 2:
            uniform_time: Vec = time_data[0] + target_step * np.arange(target_count, dtype=np.float64)
            aligned_prefix: int = min(n_samples, target_count)

            if aligned_prefix >= 2 and np.allclose(time_data[:aligned_prefix], uniform_time[:aligned_prefix], atol=1e-12):
                uniform_signal: Mat = np.asarray(y_data[:target_count, :], dtype=np.float64)
            else:
                uniform_signal = np.zeros((target_count, n_channels), dtype=np.float64)

                # Cubic splines enforce the uniform-grid assumption required by
                # the shift-invariance model behind the discrete-time pencil.
                channel_index: int = 0
                while channel_index < n_channels:
                    try:
                        spline = interpolate.CubicSpline(time_data, y_data[:, channel_index], extrapolate=False)
                        interpolated_channel: Vec = np.asarray(spline(uniform_time), dtype=np.float64)
                        finite_mask: np.ndarray = np.isfinite(interpolated_channel)

                        if np.all(finite_mask):
                            uniform_signal[:, channel_index] = interpolated_channel
                        else:
                            fallback_channel: Vec = np.interp(uniform_time, time_data, y_data[:, channel_index])
                            uniform_signal[:, channel_index] = fallback_channel.astype(np.float64)
                    except ValueError:
                        fallback_channel = np.interp(uniform_time, time_data, y_data[:, channel_index])
                        uniform_signal[:, channel_index] = fallback_channel.astype(np.float64)

                    channel_index += 1
        else:
            uniform_time = np.asarray(time_data, dtype=np.float64)
            uniform_signal = np.asarray(y_data, dtype=np.float64)
    else:
        uniform_time = np.asarray(time_data, dtype=np.float64)
        uniform_signal = np.asarray(y_data, dtype=np.float64)

    return uniform_time, uniform_signal


def select_mimo_observables(y_data: Mat,
                            observable_names: List[str] | None,
                            maximum_observables: int) -> Tuple[Mat, List[str]]:
    """
    Select the observable channels used to build the MIMO Hankel matrix.

    :param y_data: Observation matrix.
    :param observable_names: Optional channel labels.
    :param maximum_observables: Optional channel cap. ``0`` means all.
    :return: Tuple ``(selected_signal, selected_names)``.
    """
    n_channels: int = int(y_data.shape[1])
    names_list: List[str] = list()
    channel_index: int = 0

    while channel_index < n_channels:
        if observable_names is not None and channel_index < len(observable_names):
            names_list.append(str(observable_names[channel_index]))
        else:
            names_list.append(f'Observable {channel_index}')

        channel_index += 1

    if 0 < maximum_observables < n_channels:
        variances: Vec = np.var(y_data, axis=0).astype(np.float64)
        ranking_indices: np.ndarray = np.argsort(-variances, kind="stable")
        selected_indices: np.ndarray = np.sort(ranking_indices[:maximum_observables])
        selected_signal: Mat = np.asarray(y_data[:, selected_indices], dtype=np.float64)
        selected_names: List[str] = list()
        selected_index_position: int = 0

        # The full MIMO stack is preferred, but this explicit cap keeps the
        # Hankel memory bounded for very large EMT state vectors.
        while selected_index_position < selected_indices.shape[0]:
            selected_names.append(names_list[int(selected_indices[selected_index_position])])
            selected_index_position += 1
    else:
        selected_signal = np.asarray(y_data, dtype=np.float64)
        selected_names = names_list

    return selected_signal, selected_names


def fit_exponential_dc_component(time_data: Vec, signal_data: Vec) -> Vec:
    """
    Fit one decaying DC component to a single channel.

    :param time_data: Time vector.
    :param signal_data: One observation channel.
    :return: Estimated exponential offset component.
    """
    n_samples: int = int(signal_data.shape[0])

    if n_samples >= 6:
        tail_size: int = max(2, n_samples // 10)
        offset_guess: float = float(np.mean(signal_data[-tail_size:]))
        amplitude_guess: float = float(signal_data[0] - offset_guess)
        duration: float = float(time_data[-1] - time_data[0])

        if duration > 0.0:
            decay_guess: float = 5.0 / duration
        else:
            decay_guess = 1.0

        amplitude_scale: float = max(float(np.max(np.abs(signal_data))), 1.0)

        try:
            params_opt, _ = optimize.curve_fit(
                evaluate_exponential_offset_model,
                time_data,
                signal_data,
                p0=np.array([offset_guess, amplitude_guess, decay_guess], dtype=np.float64),
                bounds=(
                    np.array([-10.0 * amplitude_scale, -10.0 * amplitude_scale, 0.0], dtype=np.float64),
                    np.array([10.0 * amplitude_scale, 10.0 * amplitude_scale, 1e6], dtype=np.float64),
                ),
                maxfev=4000,
            )
            fitted_component: Vec = evaluate_exponential_offset_model(
                time_data,
                float(params_opt[0]),
                float(params_opt[1]),
                float(params_opt[2]),
            ).astype(np.float64)
        except (RuntimeError, ValueError):
            fitted_component = np.full(n_samples, offset_guess, dtype=np.float64)
    else:
        mean_value: float = float(np.mean(signal_data))
        fitted_component = np.full(n_samples, mean_value, dtype=np.float64)

    return fitted_component


def detrend_exponential_dc_offsets(time_data: Vec,
                                   y_data: Mat,
                                   use_exponential_detrending: bool) -> Mat:
    """
    Remove the exponential DC component from every observation channel.

    :param time_data: Time vector.
    :param y_data: Observation matrix.
    :param use_exponential_detrending: Enable flag.
    :return: Detrended observation matrix.
    """
    n_samples: int = int(y_data.shape[0])
    n_channels: int = int(y_data.shape[1])
    detrended_signal: Mat = np.zeros((n_samples, n_channels), dtype=np.float64)

    if use_exponential_detrending:
        channel_index: int = 0

        # Detrending frees the SVD from wasting dominant singular values on a
        # slow offset component that is not a physical oscillatory mode.
        while channel_index < n_channels:
            estimated_trend: Vec = fit_exponential_dc_component(time_data, y_data[:, channel_index])
            detrended_signal[:, channel_index] = y_data[:, channel_index] - estimated_trend
            channel_index += 1
    else:
        detrended_signal[:, :] = y_data[:, :]

    return detrended_signal


def compute_channel_scaling(y_data: Mat) -> EraChannelScaling:
    """
    Compute channel centering and scaling factors.

    :param y_data: Observation matrix.
    :return: Scaling object.
    """
    channel_means: Vec = np.mean(y_data, axis=0).astype(np.float64)
    channel_centered: Mat = (y_data - channel_means.reshape(1, -1)).astype(np.float64)
    channel_scales: Vec = np.std(channel_centered, axis=0).astype(np.float64)
    n_channels: int = int(channel_scales.shape[0])
    channel_index: int = 0

    # Standardization stabilizes the multi-output Hankel SVD and the later
    # residues are explicitly re-scaled back to the original physical units.
    while channel_index < n_channels:
        current_scale: float = float(channel_scales[channel_index])

        if current_scale > 1e-12:
            pass
        else:
            channel_scales[channel_index] = 1.0

        channel_index += 1

    return EraChannelScaling(means=channel_means, scales=channel_scales)


def standardize_signal_matrix(y_data: Mat, scaling: EraChannelScaling) -> Mat:
    """
    Standardize all channels using the provided scaling object.

    :param y_data: Observation matrix.
    :param scaling: Centering and scaling information.
    :return: Standardized observation matrix.
    """
    means: Vec = scaling.get_means()
    scales: Vec = scaling.get_scales()
    standardized_signal: Mat = ((y_data - means.reshape(1, -1)) / scales.reshape(1, -1)).astype(np.float64)
    return standardized_signal


def resolve_nominal_frequency_hz(explicit_nominal_frequency_hz: float,
                                 fallback_nominal_frequency_hz: float) -> float:
    """
    Resolve the nominal system frequency.

    :param explicit_nominal_frequency_hz: User override.
    :param fallback_nominal_frequency_hz: Grid-base fallback.
    :return: Resolved nominal frequency in Hz.
    """
    if explicit_nominal_frequency_hz > 0.0:
        nominal_frequency_hz: float = explicit_nominal_frequency_hz
    else:
        nominal_frequency_hz = fallback_nominal_frequency_hz

    if nominal_frequency_hz > 0.0:
        return nominal_frequency_hz
    else:
        return 50.0


def apply_ba_filter_matrix(y_data: Mat,
                           numerator: Vec,
                           denominator: Vec,
                           use_zero_phase_filtering: bool) -> Mat:
    """
    Apply one transfer-function filter channel-by-channel.

    :param y_data: Observation matrix.
    :param numerator: Numerator coefficients.
    :param denominator: Denominator coefficients.
    :param use_zero_phase_filtering: Use zero-phase filtering when feasible.
    :return: Filtered observation matrix.
    """
    n_samples: int = int(y_data.shape[0])
    n_channels: int = int(y_data.shape[1])
    filtered_signal: Mat = np.zeros((n_samples, n_channels), dtype=np.float64)
    channel_index: int = 0

    while channel_index < n_channels:
        current_channel: Vec = y_data[:, channel_index]

        if use_zero_phase_filtering:
            try:
                filtered_signal[:, channel_index] = signal.filtfilt(numerator, denominator, current_channel)
            except ValueError:
                filtered_signal[:, channel_index] = signal.lfilter(numerator, denominator, current_channel)
        else:
            filtered_signal[:, channel_index] = signal.lfilter(numerator, denominator, current_channel)

        channel_index += 1

    return filtered_signal


def apply_sos_filter_matrix(y_data: Mat,
                            sos_matrix: npt.NDArray[np.float64],
                            use_zero_phase_filtering: bool) -> Mat:
    """
    Apply one SOS filter channel-by-channel.

    :param y_data: Observation matrix.
    :param sos_matrix: SOS filter coefficients.
    :param use_zero_phase_filtering: Use zero-phase filtering when feasible.
    :return: Filtered observation matrix.
    """
    n_samples: int = int(y_data.shape[0])
    n_channels: int = int(y_data.shape[1])
    filtered_signal: Mat = np.zeros((n_samples, n_channels), dtype=np.float64)
    channel_index: int = 0

    while channel_index < n_channels:
        current_channel: Vec = y_data[:, channel_index]

        if use_zero_phase_filtering:
            try:
                filtered_signal[:, channel_index] = signal.sosfiltfilt(sos_matrix, current_channel)
            except ValueError:
                filtered_signal[:, channel_index] = signal.sosfilt(sos_matrix, current_channel)
        else:
            filtered_signal[:, channel_index] = signal.sosfilt(sos_matrix, current_channel)

        channel_index += 1

    return filtered_signal


def apply_notch_filter_matrix(y_data: Mat,
                              sampling_frequency_hz: float,
                              nominal_frequency_hz: float,
                              quality_factor: float,
                              use_notch_filtering: bool,
                              use_zero_phase_filtering: bool) -> Mat:
    """
    Apply the strict fundamental notch filter.

    :param y_data: Observation matrix.
    :param sampling_frequency_hz: Sampling frequency.
    :param nominal_frequency_hz: Nominal grid frequency.
    :param quality_factor: Notch quality factor.
    :param use_notch_filtering: Enable flag.
    :param use_zero_phase_filtering: Use zero-phase filtering when feasible.
    :return: Filtered observation matrix.
    """
    nyquist_hz: float = 0.5 * sampling_frequency_hz

    if use_notch_filtering and 0.0 < nominal_frequency_hz < nyquist_hz:
        normalized_frequency: float = nominal_frequency_hz / nyquist_hz

        try:
            numerator: Vec
            denominator: Vec
            numerator, denominator = signal.iirnotch(normalized_frequency, quality_factor)
            filtered_signal: Mat = apply_ba_filter_matrix(
                y_data=y_data,
                numerator=np.asarray(numerator, dtype=np.float64),
                denominator=np.asarray(denominator, dtype=np.float64),
                use_zero_phase_filtering=use_zero_phase_filtering,
            )
        except ValueError:
            filtered_signal = np.asarray(y_data, dtype=np.float64)
    else:
        filtered_signal = np.asarray(y_data, dtype=np.float64)

    return filtered_signal


def sanitize_analysis_bands(bands: Tuple[EraMatrixPencilBand, ...],
                            sampling_frequency_hz: float) -> Tuple[EraMatrixPencilBand, ...]:
    """
    Sanitize analysis bands against the current Nyquist limit.

    :param bands: Requested bands.
    :param sampling_frequency_hz: Current sampling frequency.
    :return: Sanitized tuple of bands.
    """
    sanitized_list: List[EraMatrixPencilBand] = list()
    maximum_frequency_hz: float = 0.45 * sampling_frequency_hz
    band_index: int = 0
    n_bands: int = len(bands)

    while band_index < n_bands:
        current_band: EraMatrixPencilBand = bands[band_index]
        low_hz: float = max(0.0, float(current_band.get_low_hz()))
        high_hz: float = min(float(current_band.get_high_hz()), maximum_frequency_hz)

        if high_hz > low_hz + 1.0:
            sanitized_list.append(EraMatrixPencilBand(low_hz=low_hz, high_hz=high_hz))
        else:
            pass

        band_index += 1

    if len(sanitized_list) > 0:
        return tuple(sanitized_list)
    else:
        fallback_bands: Tuple[EraMatrixPencilBand, ...] = create_default_era_analysis_bands()
        fallback_list: List[EraMatrixPencilBand] = list()
        fallback_index: int = 0
        n_fallback: int = len(fallback_bands)

        while fallback_index < n_fallback:
            fallback_band: EraMatrixPencilBand = fallback_bands[fallback_index]
            low_hz = max(0.0, float(fallback_band.get_low_hz()))
            high_hz = min(float(fallback_band.get_high_hz()), maximum_frequency_hz)

            if high_hz > low_hz + 1.0:
                fallback_list.append(EraMatrixPencilBand(low_hz=low_hz, high_hz=high_hz))
            else:
                pass

            fallback_index += 1

        if len(fallback_list) > 0:
            return tuple(fallback_list)
        else:
            return (EraMatrixPencilBand(low_hz=0.0, high_hz=max(5.0, maximum_frequency_hz)),)


def design_band_filter_sos(low_hz: float,
                           high_hz: float,
                           sampling_frequency_hz: float,
                           filter_order: int) -> npt.NDArray[np.float64] | None:
    """
    Design the real-valued sub-band filter.

    :param low_hz: Lower band edge.
    :param high_hz: Upper band edge.
    :param sampling_frequency_hz: Sampling frequency.
    :param filter_order: Butterworth order.
    :return: SOS matrix or ``None`` when the design is impossible.
    """
    nyquist_hz: float = 0.5 * sampling_frequency_hz
    safe_high_hz: float = min(high_hz, 0.98 * nyquist_hz)

    if safe_high_hz > 0.0:
        try:
            if low_hz > 0.5:
                normalized_band: Tuple[float, float] = (low_hz / nyquist_hz, safe_high_hz / nyquist_hz)
                sos_matrix: npt.NDArray[np.float64] = np.asarray(
                    signal.butter(filter_order, normalized_band, btype='bandpass', output='sos'),
                    dtype=np.float64,
                )
            else:
                normalized_cutoff: float = safe_high_hz / nyquist_hz
                sos_matrix = np.asarray(
                    signal.butter(filter_order, normalized_cutoff, btype='lowpass', output='sos'),
                    dtype=np.float64,
                )
        except ValueError:
            sos_matrix = None
    else:
        sos_matrix = None

    return sos_matrix


def compute_decimation_factor(n_samples: int,
                              input_sampling_frequency_hz: float,
                              band_high_hz: float,
                              decimation_safety_factor: float,
                              manual_cap_factor: int,
                              minimum_samples_per_band: int) -> int:
    """
    Compute the safe integer decimation factor for one band.

    :param n_samples: Number of input samples.
    :param input_sampling_frequency_hz: Input sampling frequency.
    :param band_high_hz: Upper band edge.
    :param decimation_safety_factor: Requested oversampling factor.
    :param manual_cap_factor: Legacy manual cap.
    :param minimum_samples_per_band: Minimum samples allowed after decimation.
    :return: Integer decimation factor.
    """
    target_sampling_frequency_hz: float = max(decimation_safety_factor * band_high_hz, 2.5 * band_high_hz)

    if target_sampling_frequency_hz > 0.0:
        raw_factor: int = int(math.floor(input_sampling_frequency_hz / target_sampling_frequency_hz))
    else:
        raw_factor = 1

    if raw_factor >= 1:
        decimation_factor: int = raw_factor
    else:
        decimation_factor = 1

    if manual_cap_factor > 1:
        decimation_factor = min(decimation_factor, manual_cap_factor)
    else:
        pass

    if minimum_samples_per_band > 0:
        maximum_safe_factor: int = max(1, n_samples // minimum_samples_per_band)
        decimation_factor = min(decimation_factor, maximum_safe_factor)
    else:
        pass

    if decimation_factor >= 1:
        return decimation_factor
    else:
        return 1


def prepare_band_signal(time_data: Vec,
                        y_data: Mat,
                        scaling: EraChannelScaling,
                        band: EraMatrixPencilBand,
                        era_options: EraMatrixPencilOptions) -> EraBandSignal:
    """
    Build one filtered and decimated sub-band record.

    :param time_data: Uniform time vector.
    :param y_data: Standardized and notched observation matrix.
    :param scaling: Original channel scaling information.
    :param band: Requested analysis band.
    :param era_options: Matrix-pencil options.
    :return: Prepared band record.
    """
    input_time_step: float = infer_uniform_time_step(time_data, 0.0)
    input_sampling_frequency_hz: float = 1.0 / input_time_step
    low_hz: float = float(band.get_low_hz())
    high_hz: float = float(band.get_high_hz())
    n_samples: int = int(y_data.shape[0])
    sos_matrix: npt.NDArray[np.float64] | None = design_band_filter_sos(
        low_hz=low_hz,
        high_hz=high_hz,
        sampling_frequency_hz=input_sampling_frequency_hz,
        filter_order=era_options.get_anti_alias_filter_order(),
    )

    if sos_matrix is not None:
        filtered_signal: Mat = apply_sos_filter_matrix(
            y_data=y_data,
            sos_matrix=sos_matrix,
            use_zero_phase_filtering=era_options.get_use_zero_phase_filtering(),
        )
    else:
        filtered_signal = np.asarray(y_data, dtype=np.float64)

    # A second low-pass stage acts as the explicit anti-alias barrier demanded
    # by the multi-rate specification before any integer decimation happens.
    anti_alias_cutoff_hz: float = min(high_hz * 1.02, 0.48 * input_sampling_frequency_hz)
    anti_alias_sos: npt.NDArray[np.float64] | None = design_band_filter_sos(
        low_hz=0.0,
        high_hz=anti_alias_cutoff_hz,
        sampling_frequency_hz=input_sampling_frequency_hz,
        filter_order=era_options.get_anti_alias_filter_order(),
    )

    if anti_alias_sos is not None:
        anti_aliased_signal: Mat = apply_sos_filter_matrix(
            y_data=filtered_signal,
            sos_matrix=anti_alias_sos,
            use_zero_phase_filtering=era_options.get_use_zero_phase_filtering(),
        )
    else:
        anti_aliased_signal = filtered_signal

    decimation_factor: int = compute_decimation_factor(
        n_samples=n_samples,
        input_sampling_frequency_hz=input_sampling_frequency_hz,
        band_high_hz=high_hz,
        decimation_safety_factor=era_options.get_decimation_safety_factor(),
        manual_cap_factor=era_options.get_decimation_factor(),
        minimum_samples_per_band=era_options.get_minimum_samples_per_band(),
    )

    if decimation_factor > 1:
        band_time: Vec = np.asarray(time_data[::decimation_factor], dtype=np.float64)
        band_signal: Mat = np.asarray(anti_aliased_signal[::decimation_factor, :], dtype=np.float64)
        band_time_step: float = input_time_step * decimation_factor
    else:
        band_time = np.asarray(time_data, dtype=np.float64)
        band_signal = np.asarray(anti_aliased_signal, dtype=np.float64)
        band_time_step = input_time_step

    band_sampling_frequency_hz: float = 1.0 / band_time_step
    physical_scales: Vec = scaling.get_scales()

    return EraBandSignal(
        time_data=band_time,
        signal_data=band_signal,
        physical_scales=physical_scales,
        time_step=band_time_step,
        sampling_frequency_hz=band_sampling_frequency_hz,
        low_hz=low_hz,
        high_hz=high_hz,
        decimation_factor=decimation_factor,
    )


def compute_block_rows(n_samples: int, era_options: EraMatrixPencilOptions) -> int:
    """
    Compute the block-Hankel depth.

    :param n_samples: Number of band samples.
    :param era_options: Matrix-pencil options.
    :return: Number of block rows.
    """
    ratio_based_rows: int = int(math.floor(era_options.get_block_rows_ratio() * n_samples))
    maximum_allowed_rows: int = max(2, n_samples - 2)
    candidate_rows: int = min(ratio_based_rows, maximum_allowed_rows)

    if candidate_rows >= era_options.get_minimum_block_rows():
        block_rows: int = candidate_rows
    else:
        block_rows = min(maximum_allowed_rows, era_options.get_minimum_block_rows())

    if block_rows >= 2:
        return block_rows
    else:
        return 0


def build_block_hankel_matrix(signal_data: Mat, block_rows: int) -> CxMat:
    """
    Build the MIMO block-Hankel matrix.

    :param signal_data: Band-limited MIMO observation matrix.
    :param block_rows: Number of block rows.
    :return: Complex block-Hankel matrix.
    """
    if 1 <= block_rows <= signal_data.shape[0]:
        windows = sliding_window_view(signal_data, window_shape=block_rows, axis=0)
        windows_reordered: np.ndarray = np.transpose(windows, (0, 2, 1))
        n_columns: int = int(windows_reordered.shape[0])
        n_rows: int = int(windows_reordered.shape[1] * windows_reordered.shape[2])
        hankel_matrix: CxMat = np.asarray(windows_reordered.reshape(n_columns, n_rows).T, dtype=np.complex128)
    else:
        hankel_matrix = build_empty_complex_matrix()

    return hankel_matrix


def build_forward_backward_hankel_matrix(signal_data: Mat,
                                         block_rows: int,
                                         use_forward_backward: bool) -> CxMat:
    """
    Build the forward-backward block-Hankel matrix.

    :param signal_data: Band-limited MIMO observation matrix.
    :param block_rows: Number of block rows.
    :param use_forward_backward: Enable flag.
    :return: Combined forward-backward Hankel matrix.
    """
    forward_hankel: CxMat = build_block_hankel_matrix(signal_data, block_rows)

    if use_forward_backward:
        reversed_signal: Mat = np.asarray(signal_data[::-1, :], dtype=np.float64)
        backward_hankel: CxMat = build_block_hankel_matrix(reversed_signal, block_rows)

        if forward_hankel.shape[1] == backward_hankel.shape[1]:
            combined_hankel: CxMat = np.vstack((forward_hankel, np.conjugate(backward_hankel)))
        else:
            combined_hankel = forward_hankel
    else:
        combined_hankel = forward_hankel

    return combined_hankel


def build_full_svd_decomposition(hankel_matrix: CxMat) -> EraSvdDecomposition:
    """
    Build one decomposition from a dense full SVD.

    :param hankel_matrix: Hankel matrix.
    :return: SVD decomposition object.
    """
    full_u: CxMat
    full_s: Vec
    full_vh: CxMat
    full_u, full_s, full_vh = la.svd(hankel_matrix, full_matrices=False)
    del full_u

    smallest_sigma: float = max(float(full_s[-1]), float(np.finfo(np.float64).eps))
    condition_number: float = float(full_s[0] / smallest_sigma)
    decomposition: EraSvdDecomposition = EraSvdDecomposition(
        singular_values=np.asarray(full_s, dtype=np.float64),
        right_vectors=np.asarray(full_vh.conj().T, dtype=np.complex128),
        condition_number=condition_number,
        truncated_backend=False,
    )
    return decomposition


def compute_svd_decomposition(hankel_matrix: CxMat,
                              era_options: EraMatrixPencilOptions) -> EraSvdDecomposition:
    """
    Compute the Hankel SVD using the configured backend.

    :param hankel_matrix: Forward-backward Hankel matrix.
    :param era_options: Matrix-pencil options.
    :return: SVD decomposition object.
    """
    min_dimension: int = int(min(hankel_matrix.shape[0], hankel_matrix.shape[1]))

    if min_dimension >= 2:
        use_truncated_backend: bool = (
            era_options.get_svd_solver().name == 'TruncatedRandomized' and min_dimension > max(64, 4 * era_options.get_max_modes())
        )

        if use_truncated_backend:
            requested_rank: int = min(min_dimension - 1, max(12, 4 * era_options.get_max_modes()))

            try:
                svd_u_matrix: CxMat
                singular_values: Vec
                vh_matrix: CxMat
                svd_u_matrix, singular_values, vh_matrix = spla.svds(
                    hankel_matrix,
                    k=requested_rank,
                    return_singular_vectors=True,
                )
                del svd_u_matrix

                sort_indices: np.ndarray = np.argsort(-singular_values, kind="stable")
                singular_values_sorted: Vec = np.asarray(singular_values[sort_indices], dtype=np.float64)
                right_vectors_sorted: CxMat = np.asarray(vh_matrix[sort_indices, :].conj().T, dtype=np.complex128)
                smallest_sigma: float = max(float(singular_values_sorted[-1]), float(np.finfo(np.float64).eps))
                condition_number: float = float(singular_values_sorted[0] / smallest_sigma)
                decomposition = EraSvdDecomposition(
                    singular_values=singular_values_sorted,
                    right_vectors=right_vectors_sorted,
                    condition_number=condition_number,
                    truncated_backend=True,
                )
            except (ValueError, TypeError, la.LinAlgError, spla.ArpackNoConvergence):
                decomposition = build_full_svd_decomposition(hankel_matrix)
        else:
            decomposition = build_full_svd_decomposition(hankel_matrix)
    else:
        decomposition = EraSvdDecomposition(
            singular_values=np.zeros(0, dtype=np.float64),
            right_vectors=np.zeros((0, 0), dtype=np.complex128),
            condition_number=np.inf,
            truncated_backend=False,
        )

    return decomposition


def compute_information_criterion_scores(singular_values: Vec,
                                         n_snapshots: int) -> Tuple[Vec, Vec]:
    """
    Compute MDL and AIC order-selection scores.

    :param singular_values: Singular-value vector.
    :param n_snapshots: Number of Hankel columns.
    :return: Tuple ``(mdl_scores, aic_scores)``.
    """
    n_values: int = int(singular_values.shape[0])
    mdl_scores: Vec = np.full(n_values, np.inf, dtype=np.float64)
    aic_scores: Vec = np.full(n_values, np.inf, dtype=np.float64)

    if n_values >= 2 and n_snapshots >= 2:
        covariance_eigenvalues: Vec = (singular_values * singular_values) / float(n_snapshots)
        candidate_order: int = 0

        while candidate_order < n_values - 1:
            tail_values: Vec = np.maximum(
                covariance_eigenvalues[candidate_order:],
                float(np.finfo(np.float64).eps),
            )
            tail_size: int = int(tail_values.shape[0])

            if tail_size >= 1:
                geometric_mean: float = float(np.exp(np.mean(np.log(tail_values))))
                arithmetic_mean: float = float(np.mean(tail_values))

                if arithmetic_mean > 0.0 and 0.0 < geometric_mean <= arithmetic_mean:
                    ratio_log: float = math.log(geometric_mean / arithmetic_mean)
                    mdl_scores[candidate_order] = -float(tail_size * n_snapshots) * ratio_log
                    mdl_scores[candidate_order] += 0.5 * candidate_order * (2 * n_values - candidate_order) * math.log(n_snapshots)

                    aic_scores[candidate_order] = -2.0 * float(tail_size * n_snapshots) * ratio_log
                    aic_scores[candidate_order] += 2.0 * candidate_order * (2 * n_values - candidate_order)
                else:
                    pass
            else:
                pass

            candidate_order += 1
    else:
        pass

    return mdl_scores, aic_scores


def select_model_order(decomposition: EraSvdDecomposition,
                       n_snapshots: int,
                       era_options: EraMatrixPencilOptions) -> int:
    """
    Select the effective signal subspace order.

    :param decomposition: SVD decomposition.
    :param n_snapshots: Number of Hankel columns.
    :param era_options: Matrix-pencil options.
    :return: Selected model order.
    """
    singular_values: Vec = decomposition.get_singular_values()
    n_values: int = int(singular_values.shape[0])

    if n_values >= 2:
        sigma_floor: float = max(float(np.finfo(np.float64).eps), float(singular_values[0]) * era_options.get_tol_deflation())
        conditioning_floor: float = float(singular_values[0]) / era_options.get_condition_number_limit()
        effective_floor: float = max(sigma_floor, conditioning_floor)
        effective_rank: int = int(np.sum(singular_values >= effective_floor))

        if effective_rank >= 1:
            maximum_order: int = min(era_options.get_max_modes(), effective_rank, n_values - 1)
        else:
            maximum_order = 0

        if maximum_order >= 1 and not decomposition.get_truncated_backend():
            mdl_scores: Vec
            aic_scores: Vec
            mdl_scores, aic_scores = compute_information_criterion_scores(singular_values[:effective_rank], n_snapshots)
            best_mdl_order: int = int(np.argmin(mdl_scores[:maximum_order + 1]))

            if np.isfinite(mdl_scores[best_mdl_order]):
                selected_order: int = best_mdl_order
            else:
                best_aic_order: int = int(np.argmin(aic_scores[:maximum_order + 1]))

                if np.isfinite(aic_scores[best_aic_order]):
                    selected_order = best_aic_order
                else:
                    selected_order = 0
        else:
            selected_order = 0

        if selected_order == 0 and maximum_order >= 1:
            singular_value_ratios: Vec = np.ones(maximum_order, dtype=np.float64)
            ratio_index: int = 0

            # The truncated backend does not expose the full noise tail, so a
            # conservative singular-gap fallback is used when MDL/AIC is unsafe.
            while ratio_index < maximum_order:
                numerator: float = float(singular_values[ratio_index])
                denominator: float = max(float(singular_values[ratio_index + 1]), float(np.finfo(np.float64).eps))
                singular_value_ratios[ratio_index] = numerator / denominator
                ratio_index += 1

            selected_order = int(np.argmax(singular_value_ratios)) + 1
        else:
            pass

        selected_order = min(selected_order, maximum_order)
    else:
        selected_order = 0

    if selected_order >= 1:
        return selected_order
    else:
        return 0


def build_square_tls_pencil(right_vectors: CxMat, selected_order: int) -> Tuple[CxMat, CxMat]:
    """
    Build the square TLS pencil used by the generalized eigenproblem.

    :param right_vectors: Right singular vectors as columns.
    :param selected_order: Effective model order.
    :return: Tuple ``(V2, V1)`` of square matrices.
    """
    n_rows: int = int(right_vectors.shape[0])
    order: int = min(selected_order, right_vectors.shape[1])

    if order >= 1 and n_rows >= order + 1:
        tall_v1: CxMat = np.asarray(right_vectors[:-1, :order], dtype=np.complex128)
        tall_v2: CxMat = np.asarray(right_vectors[1:, :order], dtype=np.complex128)

        # The QR reduction preserves the tall shift-invariance relation while
        # transforming it into a square pencil suitable for the QZ algorithm.
        q_matrix: CxMat
        r_matrix: CxMat
        q_matrix, r_matrix = la.qr(tall_v1, mode='economic')
        reduced_v2: CxMat = np.asarray(q_matrix.conj().T @ tall_v2, dtype=np.complex128)
        return reduced_v2, np.asarray(r_matrix, dtype=np.complex128)
    else:
        return build_empty_complex_matrix(), build_empty_complex_matrix()


def build_candidate_orders(maximum_order: int) -> IntVec:
    """
    Build the candidate orders explored inside one band.

    :param maximum_order: Upper-order bound supplied by the IC stage.
    :return: Integer vector of candidate orders.
    """
    if maximum_order >= 2:
        candidate_list: List[int] = list()
        candidate_order: int = 2

        # Real oscillatory modes naturally appear in conjugate pairs, so the
        # band sweep explores even orders first to favor physically sparse models.
        while candidate_order <= maximum_order:
            candidate_list.append(candidate_order)
            candidate_order += 2

        if maximum_order % 2 == 1:
            candidate_list.append(maximum_order)
        else:
            pass

        return np.asarray(candidate_list, dtype=np.int_)
    elif maximum_order == 1:
        return np.asarray([1], dtype=np.int_)
    else:
        return np.zeros(0, dtype=np.int_)


def reject_notched_nominal_poles(z_poles: CxVec,
                                 s_poles: CxVec,
                                 era_options: EraMatrixPencilOptions) -> Tuple[CxVec, CxVec]:
    """
    Remove poles that remain too close to the notched nominal frequency.

    :param z_poles: Discrete-time poles.
    :param s_poles: Continuous-time poles.
    :param era_options: Matrix-pencil options.
    :return: Tuple ``(filtered_z_poles, filtered_s_poles)``.
    """
    nominal_frequency_hz: float = era_options.get_nominal_frequency_hz()

    if era_options.get_use_notch_filtering() and nominal_frequency_hz > 0.0 and s_poles.shape[0] > 0:
        pole_frequencies_hz: Vec = np.abs(np.imag(s_poles)) / (2.0 * np.pi)
        rejection_half_width_hz: float = max(2.0, 2.0 * era_options.get_principal_log_tolerance_hz())
        keep_mask: np.ndarray = np.abs(pole_frequencies_hz - nominal_frequency_hz) > rejection_half_width_hz

        if np.any(keep_mask):
            filtered_z_poles: CxVec = np.asarray(z_poles[keep_mask], dtype=np.complex128)
            filtered_s_poles: CxVec = np.asarray(s_poles[keep_mask], dtype=np.complex128)
        else:
            filtered_z_poles = build_empty_complex_vector()
            filtered_s_poles = build_empty_complex_vector()
    else:
        filtered_z_poles = np.asarray(z_poles, dtype=np.complex128)
        filtered_s_poles = np.asarray(s_poles, dtype=np.complex128)

    return filtered_z_poles, filtered_s_poles


def reject_excessively_fast_poles(z_poles: CxVec,
                                  s_poles: CxVec,
                                  record_duration_s: float) -> Tuple[CxVec, CxVec]:
    """
    Reject poles whose real part is too extreme for the available record length.

    :param z_poles: Discrete-time poles.
    :param s_poles: Continuous-time poles.
    :param record_duration_s: Available record length in seconds.
    :return: Tuple ``(filtered_z_poles, filtered_s_poles)``.
    """
    if record_duration_s > 0.0 and s_poles.shape[0] > 0:
        maximum_abs_real_part: float = 15.0 / record_duration_s
        keep_mask: np.ndarray = np.abs(np.real(s_poles)) <= maximum_abs_real_part

        # Extremely fast growth or decay across a short record is normally a
        # numerical artefact of the pencil rather than a physically observable EMT mode.
        if np.any(keep_mask):
            filtered_z_poles: CxVec = np.asarray(z_poles[keep_mask], dtype=np.complex128)
            filtered_s_poles: CxVec = np.asarray(s_poles[keep_mask], dtype=np.complex128)
        else:
            filtered_z_poles = build_empty_complex_vector()
            filtered_s_poles = build_empty_complex_vector()
    else:
        filtered_z_poles = np.asarray(z_poles, dtype=np.complex128)
        filtered_s_poles = np.asarray(s_poles, dtype=np.complex128)

    return filtered_z_poles, filtered_s_poles


def solve_band_modes_for_order(band_signal: EraBandSignal,
                               era_options: EraMatrixPencilOptions,
                               decomposition: EraSvdDecomposition,
                               candidate_order: int) -> EraBandResult:
    """
    Solve one band for one explicit candidate order.

    :param band_signal: Prepared band record.
    :param era_options: Matrix-pencil options.
    :param decomposition: Band SVD decomposition.
    :param candidate_order: Explicit candidate order.
    :return: One band result for that candidate order.
    """
    signal_data: Mat = band_signal.get_signal_data()
    observable_count: int = int(signal_data.shape[1])
    low_hz: float = band_signal.get_low_hz()
    high_hz: float = band_signal.get_high_hz()
    record_duration_s: float = 0.0

    if band_signal.get_time_data().shape[0] >= 2:
        record_duration_s = float(band_signal.get_time_data()[-1] - band_signal.get_time_data()[0])
    else:
        record_duration_s = 0.0

    right_vectors: CxMat = decomposition.get_right_vectors()
    v2_matrix: CxMat
    v1_matrix: CxMat
    v2_matrix, v1_matrix = build_square_tls_pencil(right_vectors, candidate_order)

    if v1_matrix.shape[0] >= 1:
        raw_z_poles: CxVec = solve_tls_gevp(v2_matrix=v2_matrix, v1_matrix=v1_matrix)
        filtered_z_poles: CxVec = filter_discrete_poles(raw_z_poles)

        if filtered_z_poles.shape[0] > 0:
            valid_z_poles: CxVec
            valid_s_poles: CxVec
            valid_z_poles, valid_s_poles = map_discrete_to_continuous_poles(
                z_poles=filtered_z_poles,
                time_step=band_signal.get_time_step(),
                low_hz=low_hz,
                high_hz=high_hz,
                principal_log_tolerance_hz=era_options.get_principal_log_tolerance_hz(),
            )

            if valid_s_poles.shape[0] > 0:
                valid_z_poles, valid_s_poles = reject_notched_nominal_poles(
                    z_poles=valid_z_poles,
                    s_poles=valid_s_poles,
                    era_options=era_options,
                )

                if valid_s_poles.shape[0] > 0:
                    valid_z_poles, valid_s_poles = reject_excessively_fast_poles(
                        z_poles=valid_z_poles,
                        s_poles=valid_s_poles,
                        record_duration_s=record_duration_s,
                    )

                    if valid_s_poles.shape[0] > 0:
                        pass
                    else:
                        return create_empty_band_result(observable_count, low_hz, high_hz)

                    unique_z_poles: CxVec
                    unique_s_poles: CxVec
                    unique_z_poles, unique_s_poles = deduplicate_continuous_poles(
                        z_poles=valid_z_poles,
                        s_poles=valid_s_poles,
                        frequency_tolerance_hz=0.5 * era_options.get_frequency_merge_tolerance_hz(),
                        real_part_tolerance=0.5 * era_options.get_real_part_merge_tolerance(),
                    )
                    unique_z_poles, unique_s_poles = enforce_conjugate_symmetry(
                        z_poles=unique_z_poles,
                        s_poles=unique_s_poles,
                        time_step=band_signal.get_time_step(),
                        frequency_tolerance_hz=0.5 * era_options.get_frequency_merge_tolerance_hz(),
                        real_part_tolerance=0.5 * era_options.get_real_part_merge_tolerance(),
                    )

                    if unique_s_poles.shape[0] > 0:
                        standardized_residues: CxMat
                        reconstruction_error: float
                        standardized_residues, reconstruction_error = solve_modal_residues(
                            signal_data=signal_data,
                            z_poles=unique_z_poles,
                        )
                        physical_residues: CxMat = scale_residues_to_physical_units(
                            residues=standardized_residues,
                            physical_scales=band_signal.get_physical_scales(),
                        )
                        physical_signal_data: CxMat = build_physical_band_signal(
                            signal_data=signal_data,
                            physical_scales=band_signal.get_physical_scales(),
                        )
                        modal_energy: Vec = compute_modal_energies(
                            physical_signal_data=physical_signal_data,
                            z_poles=unique_z_poles,
                            physical_residues=physical_residues,
                        )
                        keep_mask: np.ndarray = compute_pair_energy_keep_mask(
                            s_poles=unique_s_poles,
                            modal_energy=modal_energy,
                            energy_threshold=era_options.get_min_mode_energy_ratio(),
                            frequency_tolerance_hz=0.5 * era_options.get_frequency_merge_tolerance_hz(),
                            real_part_tolerance=0.5 * era_options.get_real_part_merge_tolerance(),
                        )

                        if np.any(keep_mask):
                            kept_z_poles: CxVec = np.asarray(unique_z_poles[keep_mask], dtype=np.complex128)
                            kept_s_poles: CxVec = np.asarray(unique_s_poles[keep_mask], dtype=np.complex128)
                            refined_residues: CxMat
                            refined_error: float
                            refined_residues, refined_error = solve_modal_residues(
                                signal_data=signal_data,
                                z_poles=kept_z_poles,
                            )
                            physical_refined_residues: CxMat = scale_residues_to_physical_units(
                                residues=refined_residues,
                                physical_scales=band_signal.get_physical_scales(),
                            )
                            refined_energy: Vec = compute_modal_energies(
                                physical_signal_data=physical_signal_data,
                                z_poles=kept_z_poles,
                                physical_residues=physical_refined_residues,
                            )

                            return EraBandResult(
                                poles_s=kept_s_poles,
                                poles_z=kept_z_poles,
                                residues=physical_refined_residues,
                                modal_energy=refined_energy,
                                reconstruction_error=refined_error,
                                band_low_hz=low_hz,
                                band_high_hz=high_hz,
                                selected_order=candidate_order,
                                observable_count=observable_count,
                                condition_number=decomposition.get_condition_number(),
                                successful=True,
                            )
                        else:
                            return create_empty_band_result(observable_count, low_hz, high_hz)
                    else:
                        return create_empty_band_result(observable_count, low_hz, high_hz)
                else:
                    return create_empty_band_result(observable_count, low_hz, high_hz)
            else:
                return create_empty_band_result(observable_count, low_hz, high_hz)
        else:
            return create_empty_band_result(observable_count, low_hz, high_hz)
    else:
        return create_empty_band_result(observable_count, low_hz, high_hz)


def compute_band_result_score(band_result: EraBandResult) -> float:
    """
    Compute the selection score used to choose the best candidate order.

    :param band_result: Candidate band result.
    :return: Scalar score. Larger is better.
    """
    poles_s: CxVec = band_result.get_poles_s()
    modal_energy: Vec = band_result.get_modal_energy()

    if band_result.get_successful() and 0 < poles_s.shape[0] == modal_energy.shape[0]:
        real_part_weight: Vec = 1.0 + np.abs(np.real(poles_s))
        persistence_energy: Vec = modal_energy / real_part_weight
        score_value: float = float(np.sum(persistence_energy) / float(poles_s.shape[0]))
    else:
        score_value = -1.0

    return score_value


def solve_tls_gevp(v2_matrix: CxMat, v1_matrix: CxMat) -> CxVec:
    """
    Solve the TLS generalized eigenvalue problem with a QZ-based backend.

    :param v2_matrix: Upper pencil matrix.
    :param v1_matrix: Lower pencil matrix.
    :return: Discrete-time pole vector.
    """
    matrix_size: int = int(v1_matrix.shape[0])

    if matrix_size >= 1 and v2_matrix.shape == v1_matrix.shape:
        try:
            homogeneous_roots_raw = la.eig(v2_matrix, v1_matrix, right=False, homogeneous_eigvals=True)
            homogeneous_roots: CxMat = np.asarray(homogeneous_roots_raw, dtype=np.complex128)
            alpha_values: CxVec = np.asarray(homogeneous_roots[0], dtype=np.complex128)
            beta_values: CxVec = np.asarray(homogeneous_roots[1], dtype=np.complex128)
            valid_mask: np.ndarray = np.abs(beta_values) > 1e-14

            if np.any(valid_mask):
                z_poles: CxVec = np.asarray(alpha_values[valid_mask] / beta_values[valid_mask], dtype=np.complex128)
            else:
                z_poles = build_empty_complex_vector()
        except (TypeError, ValueError, la.LinAlgError):
            try:
                z_poles = np.asarray(la.eig(v2_matrix, v1_matrix, right=False), dtype=np.complex128)
            except (TypeError, ValueError, la.LinAlgError):
                z_poles = build_empty_complex_vector()
    else:
        z_poles = build_empty_complex_vector()

    return z_poles


def filter_discrete_poles(z_poles: CxVec) -> CxVec:
    """
    Remove obviously invalid discrete-time poles.

    :param z_poles: Raw generalized eigenvalues.
    :return: Sanitized discrete pole vector.
    """
    if z_poles.shape[0] > 0:
        finite_mask: np.ndarray = np.isfinite(np.real(z_poles)) & np.isfinite(np.imag(z_poles))
        magnitude_mask: np.ndarray = (np.abs(z_poles) > 1e-14) & (np.abs(z_poles) < 1e8)
        combined_mask: np.ndarray = finite_mask & magnitude_mask

        if np.any(combined_mask):
            filtered_poles: CxVec = np.asarray(z_poles[combined_mask], dtype=np.complex128)
        else:
            filtered_poles = build_empty_complex_vector()
    else:
        filtered_poles = build_empty_complex_vector()

    return filtered_poles


def map_discrete_to_continuous_poles(z_poles: CxVec,
                                     time_step: float,
                                     low_hz: float,
                                     high_hz: float,
                                     principal_log_tolerance_hz: float) -> Tuple[CxVec, CxVec]:
    """
    Map discrete-time poles to continuous time and validate the principal log.

    :param z_poles: Discrete-time poles.
    :param time_step: Effective time step.
    :param low_hz: Lower band edge.
    :param high_hz: Upper band edge.
    :param principal_log_tolerance_hz: Validation tolerance in Hz.
    :return: Tuple ``(valid_z_poles, valid_s_poles)``.
    """
    if z_poles.shape[0] > 0 and time_step > 0.0:
        s_poles: CxVec = np.asarray(np.log(z_poles) / time_step, dtype=np.complex128)
        frequencies_hz: Vec = np.abs(np.imag(s_poles)) / (2.0 * np.pi)
        nyquist_hz: float = 0.5 / time_step
        valid_mask: np.ndarray = frequencies_hz <= (nyquist_hz - principal_log_tolerance_hz)
        valid_mask = valid_mask & (frequencies_hz >= max(0.0, low_hz - principal_log_tolerance_hz))
        valid_mask = valid_mask & (frequencies_hz <= (high_hz + principal_log_tolerance_hz))

        # A thin guard below Nyquist removes common chatter artefacts created by
        # time-domain integrators rather than by the physical EMT model.
        valid_mask = valid_mask & (frequencies_hz <= 0.98 * nyquist_hz)

        if np.any(valid_mask):
            valid_z_poles: CxVec = np.asarray(z_poles[valid_mask], dtype=np.complex128)
            valid_s_poles: CxVec = np.asarray(s_poles[valid_mask], dtype=np.complex128)
        else:
            valid_z_poles = build_empty_complex_vector()
            valid_s_poles = build_empty_complex_vector()
    else:
        valid_z_poles = build_empty_complex_vector()
        valid_s_poles = build_empty_complex_vector()

    return valid_z_poles, valid_s_poles


def deduplicate_continuous_poles(z_poles: CxVec,
                                 s_poles: CxVec,
                                 frequency_tolerance_hz: float,
                                 real_part_tolerance: float) -> Tuple[CxVec, CxVec]:
    """
    Remove duplicate poles inside one band.

    :param z_poles: Discrete-time poles.
    :param s_poles: Continuous-time poles.
    :param frequency_tolerance_hz: Frequency tolerance in Hz.
    :param real_part_tolerance: Real-part tolerance in 1/s.
    :return: Tuple ``(unique_z_poles, unique_s_poles)``.
    """
    n_modes: int = int(s_poles.shape[0])

    if n_modes > 0:
        used_mask: np.ndarray = np.zeros(n_modes, dtype=np.bool_)
        unique_z_list: List[complex] = list()
        unique_s_list: List[complex] = list()
        mode_index: int = 0

        while mode_index < n_modes:
            if not used_mask[mode_index]:
                reference_pole: complex = complex(s_poles[mode_index])
                used_mask[mode_index] = True
                unique_z_list.append(complex(z_poles[mode_index]))
                unique_s_list.append(reference_pole)
                candidate_index: int = mode_index + 1

                while candidate_index < n_modes:
                    if not used_mask[candidate_index]:
                        candidate_pole: complex = complex(s_poles[candidate_index])
                        frequency_delta_hz: float = abs(float(np.imag(candidate_pole - reference_pole)) / (2.0 * np.pi))
                        real_delta: float = abs(float(np.real(candidate_pole - reference_pole)))

                        if frequency_delta_hz <= frequency_tolerance_hz and real_delta <= real_part_tolerance:
                            used_mask[candidate_index] = True
                        else:
                            pass
                    else:
                        pass

                    candidate_index += 1
            else:
                pass

            mode_index += 1

        unique_z_poles: CxVec = np.asarray(unique_z_list, dtype=np.complex128)
        unique_s_poles: CxVec = np.asarray(unique_s_list, dtype=np.complex128)
    else:
        unique_z_poles = build_empty_complex_vector()
        unique_s_poles = build_empty_complex_vector()

    return unique_z_poles, unique_s_poles


def find_conjugate_index(s_poles: CxVec,
                         reference_index: int,
                         frequency_tolerance_hz: float,
                         real_part_tolerance: float) -> int:
    """
    Find the conjugate partner of one pole.

    :param s_poles: Continuous-time poles.
    :param reference_index: Reference pole index.
    :param frequency_tolerance_hz: Frequency tolerance in Hz.
    :param real_part_tolerance: Real-part tolerance in 1/s.
    :return: Matching index or ``-1``.
    """
    reference_pole: complex = complex(s_poles[reference_index])
    target_pole: complex = np.conjugate(reference_pole)
    n_modes: int = int(s_poles.shape[0])
    candidate_index: int = 0

    while candidate_index < n_modes:
        if candidate_index != reference_index:
            candidate_pole: complex = complex(s_poles[candidate_index])
            frequency_delta_hz: float = abs(float(np.imag(candidate_pole - target_pole)) / (2.0 * np.pi))
            real_delta: float = abs(float(np.real(candidate_pole - target_pole)))

            if frequency_delta_hz <= frequency_tolerance_hz and real_delta <= real_part_tolerance:
                return candidate_index
            else:
                pass
        else:
            pass

        candidate_index += 1

    return -1


def enforce_conjugate_symmetry(z_poles: CxVec,
                               s_poles: CxVec,
                               time_step: float,
                               frequency_tolerance_hz: float,
                               real_part_tolerance: float) -> Tuple[CxVec, CxVec]:
    """
    Enforce explicit conjugate-pair symmetry for real-valued EMT signals.

    :param z_poles: Discrete-time poles.
    :param s_poles: Continuous-time poles.
    :param time_step: Effective time step.
    :param frequency_tolerance_hz: Frequency tolerance in Hz.
    :param real_part_tolerance: Real-part tolerance in 1/s.
    :return: Tuple ``(symmetrized_z_poles, symmetrized_s_poles)``.
    """
    n_modes: int = int(s_poles.shape[0])

    if n_modes > 0:
        z_list: List[complex] = list(z_poles.tolist())
        s_list: List[complex] = list(s_poles.tolist())
        mode_index: int = 0

        while mode_index < n_modes:
            current_pole: complex = complex(s_poles[mode_index])

            if abs(float(np.imag(current_pole))) > 1e-9:
                conjugate_index: int = find_conjugate_index(
                    s_poles=s_poles,
                    reference_index=mode_index,
                    frequency_tolerance_hz=frequency_tolerance_hz,
                    real_part_tolerance=real_part_tolerance,
                )

                if conjugate_index >= 0:
                    pass
                else:
                    conjugate_pole_s: complex = np.conjugate(current_pole)
                    conjugate_pole_z: complex = complex(np.exp(conjugate_pole_s * time_step))
                    s_list.append(conjugate_pole_s)
                    z_list.append(conjugate_pole_z)
            else:
                pass

            mode_index += 1

        symmetrized_z_poles: CxVec = np.asarray(z_list, dtype=np.complex128)
        symmetrized_s_poles: CxVec = np.asarray(s_list, dtype=np.complex128)
        symmetrized_z_poles, symmetrized_s_poles = deduplicate_continuous_poles(
            z_poles=symmetrized_z_poles,
            s_poles=symmetrized_s_poles,
            frequency_tolerance_hz=frequency_tolerance_hz,
            real_part_tolerance=real_part_tolerance,
        )
    else:
        symmetrized_z_poles = build_empty_complex_vector()
        symmetrized_s_poles = build_empty_complex_vector()

    return symmetrized_z_poles, symmetrized_s_poles


def build_vandermonde_matrix(z_poles: CxVec, n_samples: int) -> CxMat:
    """
    Build the Vandermonde matrix used to fit modal residues.

    :param z_poles: Discrete-time poles.
    :param n_samples: Number of time samples.
    :return: Complex Vandermonde matrix.
    """
    n_modes: int = int(z_poles.shape[0])
    vandermonde_matrix: CxMat = np.zeros((n_samples, n_modes), dtype=np.complex128)

    if n_modes > 0 and n_samples > 0:
        vandermonde_matrix[0, :] = 1.0 + 0.0j
        sample_index: int = 1

        # Recursive construction is used instead of repeated powers to reduce
        # both overhead and numerical spread for long ringdowns.
        while sample_index < n_samples:
            vandermonde_matrix[sample_index, :] = vandermonde_matrix[sample_index - 1, :] * z_poles
            sample_index += 1
    else:
        pass

    return vandermonde_matrix


def solve_modal_residues(signal_data: Mat, z_poles: CxVec) -> Tuple[CxMat, float]:
    """
    Solve the MIMO residue least-squares problem.

    :param signal_data: Standardized band-limited signal matrix.
    :param z_poles: Discrete-time poles.
    :return: Tuple ``(residues, reconstruction_error)``.
    """
    n_samples: int = int(signal_data.shape[0])
    n_channels: int = int(signal_data.shape[1])
    n_modes: int = int(z_poles.shape[0])

    if n_modes > 0 and n_samples > 0 and n_channels > 0:
        vandermonde_matrix: CxMat = build_vandermonde_matrix(z_poles, n_samples)

        try:
            residues: CxMat
            residual_vector: CxVec
            numerical_rank: int
            singular_values: Vec
            residues, residual_vector, numerical_rank, singular_values = la.lstsq(
                vandermonde_matrix,
                np.asarray(signal_data, dtype=np.complex128),
            )
            reconstructed_signal: CxMat = np.asarray(vandermonde_matrix @ residues, dtype=np.complex128)
            residual_norm: float = float(np.linalg.norm(np.asarray(signal_data, dtype=np.complex128) - reconstructed_signal, ord='fro'))
            signal_norm: float = max(float(np.linalg.norm(np.asarray(signal_data, dtype=np.complex128), ord='fro')), 1e-12)
            reconstruction_error: float = residual_norm / signal_norm
            del residual_vector
            del numerical_rank
            del singular_values
        except (ValueError, la.LinAlgError):
            residues = np.zeros((n_modes, n_channels), dtype=np.complex128)
            reconstruction_error = 1.0
    else:
        residues = build_empty_complex_matrix()
        reconstruction_error = 1.0

    return residues, reconstruction_error


def scale_residues_to_physical_units(residues: CxMat, physical_scales: Vec) -> CxMat:
    """
    Re-scale residues back to the original physical channel magnitudes.

    :param residues: Standardized residue matrix.
    :param physical_scales: Original per-channel scales.
    :return: Physical residue matrix.
    """
    if residues.shape[0] > 0 and residues.shape[1] > 0:
        physical_residues: CxMat = np.asarray(residues * physical_scales.reshape(1, -1), dtype=np.complex128)
    else:
        physical_residues = build_empty_complex_matrix()

    return physical_residues


def build_physical_band_signal(signal_data: Mat, physical_scales: Vec) -> CxMat:
    """
    Re-scale the band-limited observations back to physical units.

    :param signal_data: Standardized band-limited observation matrix.
    :param physical_scales: Original per-channel scales.
    :return: Physical complex signal matrix.
    """
    if signal_data.shape[0] > 0 and signal_data.shape[1] > 0:
        physical_signal: CxMat = np.asarray(signal_data * physical_scales.reshape(1, -1), dtype=np.complex128)
    else:
        physical_signal = build_empty_complex_matrix()

    return physical_signal


def compute_modal_energies(physical_signal_data: CxMat,
                           z_poles: CxVec,
                           physical_residues: CxMat) -> Vec:
    """
    Compute per-mode modal energy in physical units.

    :param physical_signal_data: Physical band-limited observations.
    :param z_poles: Discrete-time poles.
    :param physical_residues: Physical residue matrix.
    :return: Relative modal-energy vector.
    """
    n_samples: int = int(physical_signal_data.shape[0])
    n_modes: int = int(z_poles.shape[0])
    modal_energy: Vec = np.zeros(n_modes, dtype=np.float64)

    if n_modes > 0 and n_samples > 0:
        vandermonde_matrix: CxMat = build_vandermonde_matrix(z_poles, n_samples)
        total_energy: float = max(float(np.linalg.norm(physical_signal_data, ord='fro') ** 2), 1e-12)
        mode_index: int = 0

        # Each mode is evaluated independently so low-energy artefacts can be
        # pruned before the cross-band fusion step happens.
        while mode_index < n_modes:
            mode_response: CxMat = np.asarray(
                vandermonde_matrix[:, mode_index:mode_index + 1] @ physical_residues[mode_index:mode_index + 1, :],
                dtype=np.complex128,
            )
            modal_energy[mode_index] = float(np.linalg.norm(mode_response, ord='fro') ** 2) / total_energy
            mode_index += 1
    else:
        pass

    return modal_energy


def compute_pair_energy_keep_mask(s_poles: CxVec,
                                  modal_energy: Vec,
                                  energy_threshold: float,
                                  frequency_tolerance_hz: float,
                                  real_part_tolerance: float) -> np.ndarray:
    """
    Build the keep mask while preserving conjugate pairs.

    :param s_poles: Continuous-time poles.
    :param modal_energy: Relative modal-energy vector.
    :param energy_threshold: Minimum retained energy.
    :param frequency_tolerance_hz: Frequency tolerance in Hz.
    :param real_part_tolerance: Real-part tolerance in 1/s.
    :return: Boolean keep mask.
    """
    n_modes: int = int(s_poles.shape[0])
    keep_mask: np.ndarray = np.zeros(n_modes, dtype=np.bool_)
    mode_index: int = 0

    while mode_index < n_modes:
        conjugate_index: int = find_conjugate_index(
            s_poles=s_poles,
            reference_index=mode_index,
            frequency_tolerance_hz=frequency_tolerance_hz,
            real_part_tolerance=real_part_tolerance,
        )

        if conjugate_index >= 0:
            pair_energy: float = float(modal_energy[mode_index] + modal_energy[conjugate_index])

            if pair_energy >= energy_threshold:
                keep_mask[mode_index] = True
                keep_mask[conjugate_index] = True
            else:
                pass
        else:
            if modal_energy[mode_index] >= energy_threshold:
                keep_mask[mode_index] = True
            else:
                pass

        mode_index += 1

    return keep_mask


def extract_band_modes(band_signal: EraBandSignal,
                       era_options: EraMatrixPencilOptions) -> EraBandResult:
    """
    Extract one band of modes using the TLS forward-backward matrix pencil.

    :param band_signal: Prepared band record.
    :param era_options: Matrix-pencil options.
    :return: One independent band result.
    """
    signal_data: Mat = band_signal.get_signal_data()
    n_samples: int = int(signal_data.shape[0])
    observable_count: int = int(signal_data.shape[1])
    low_hz: float = band_signal.get_low_hz()
    high_hz: float = band_signal.get_high_hz()

    if n_samples >= era_options.get_minimum_samples_per_band() and observable_count > 0:
        block_rows: int = compute_block_rows(n_samples, era_options)

        if block_rows >= 2:
            hankel_matrix: CxMat = build_forward_backward_hankel_matrix(
                signal_data=signal_data,
                block_rows=block_rows,
                use_forward_backward=era_options.get_use_forward_backward(),
            )

            if hankel_matrix.shape[0] > 0 and hankel_matrix.shape[1] >= 2:
                decomposition: EraSvdDecomposition = compute_svd_decomposition(hankel_matrix, era_options)
                maximum_order: int = select_model_order(
                    decomposition=decomposition,
                    n_snapshots=int(hankel_matrix.shape[1]),
                    era_options=era_options,
                )

                if maximum_order >= 1:
                    candidate_orders: IntVec = build_candidate_orders(maximum_order)
                    candidate_index: int = 0
                    n_candidates: int = int(candidate_orders.shape[0])
                    best_result: EraBandResult = create_empty_band_result(observable_count, low_hz, high_hz)
                    best_score: float = -1.0

                    while candidate_index < n_candidates:
                        candidate_order: int = int(candidate_orders[candidate_index])
                        candidate_result: EraBandResult = solve_band_modes_for_order(
                            band_signal=band_signal,
                            era_options=era_options,
                            decomposition=decomposition,
                            candidate_order=candidate_order,
                        )
                        candidate_score: float = compute_band_result_score(candidate_result)

                        if candidate_score > best_score:
                            best_result = candidate_result
                            best_score = candidate_score
                        else:
                            pass

                        candidate_index += 1

                    if best_result.get_successful() and best_result.get_poles_s().shape[0] > 0:
                        return best_result
                    else:
                        return create_empty_band_result(observable_count, low_hz, high_hz)
                else:
                    return create_empty_band_result(observable_count, low_hz, high_hz)
            else:
                return create_empty_band_result(observable_count, low_hz, high_hz)
        else:
            return create_empty_band_result(observable_count, low_hz, high_hz)
    else:
        return create_empty_band_result(observable_count, low_hz, high_hz)


def sort_modes_by_frequency_and_damping(poles_s: CxVec,
                                        residues: CxMat,
                                        modal_energy: Vec,
                                        reconstruction_errors: Vec,
                                        band_low_hz: Vec,
                                        band_high_hz: Vec,
                                        selected_orders: IntVec,
                                        observable_count_per_mode: IntVec) -> EraMergedModalData:
    """
    Sort fused modes by absolute frequency and then by damping.

    :param poles_s: Pole vector.
    :param residues: Residue matrix.
    :param modal_energy: Modal-energy vector.
    :param reconstruction_errors: Reconstruction-error vector.
    :param band_low_hz: Lower-band vector.
    :param band_high_hz: Upper-band vector.
    :param selected_orders: Selected-order vector.
    :param observable_count_per_mode: Observable-count vector.
    :return: Sorted merged modal data.
    """
    n_modes: int = int(poles_s.shape[0])

    if n_modes > 0:
        frequencies_hz: Vec = np.abs(np.imag(poles_s)) / (2.0 * np.pi)
        sort_indices: np.ndarray = np.lexsort((np.real(poles_s), frequencies_hz))

        return EraMergedModalData(
            poles_s=np.asarray(poles_s[sort_indices], dtype=np.complex128),
            residues=np.asarray(residues[sort_indices, :], dtype=np.complex128),
            modal_energy=np.asarray(modal_energy[sort_indices], dtype=np.float64),
            reconstruction_errors=np.asarray(reconstruction_errors[sort_indices], dtype=np.float64),
            band_low_hz=np.asarray(band_low_hz[sort_indices], dtype=np.float64),
            band_high_hz=np.asarray(band_high_hz[sort_indices], dtype=np.float64),
            selected_orders=np.asarray(selected_orders[sort_indices], dtype=np.int_),
            observable_count_per_mode=np.asarray(observable_count_per_mode[sort_indices], dtype=np.int_),
        )
    else:
        return create_empty_merged_modal_data()


def merge_band_results(band_results: List[EraBandResult],
                       era_options: EraMatrixPencilOptions) -> EraMergedModalData:
    """
    Fuse the valid band results into one modal set.

    :param band_results: List of band results.
    :param era_options: Matrix-pencil options.
    :return: Fused modal data.
    """
    valid_results: List[EraBandResult] = list()
    band_index: int = 0
    n_results: int = len(band_results)

    while band_index < n_results:
        current_result: EraBandResult = band_results[band_index]

        if current_result.get_successful() and current_result.get_poles_s().shape[0] > 0:
            valid_results.append(current_result)
        else:
            pass

        band_index += 1

    if len(valid_results) > 0:
        poles_list: List[complex] = list()
        residue_list: List[np.ndarray] = list()
        energy_list: List[float] = list()
        error_list: List[float] = list()
        band_low_list: List[float] = list()
        band_high_list: List[float] = list()
        selected_order_list: List[int] = list()
        observable_count_list: List[int] = list()
        result_index: int = 0

        while result_index < len(valid_results):
            current_result = valid_results[result_index]
            current_poles: CxVec = current_result.get_poles_s()
            current_residues: CxMat = current_result.get_residues()
            current_energy: Vec = current_result.get_modal_energy()
            mode_index: int = 0
            n_modes: int = int(current_poles.shape[0])

            while mode_index < n_modes:
                poles_list.append(complex(current_poles[mode_index]))
                residue_list.append(np.asarray(current_residues[mode_index, :], dtype=np.complex128))
                energy_list.append(float(current_energy[mode_index]))
                error_list.append(float(current_result.get_reconstruction_error()))
                band_low_list.append(float(current_result.get_band_low_hz()))
                band_high_list.append(float(current_result.get_band_high_hz()))
                selected_order_list.append(int(current_result.get_selected_order()))
                observable_count_list.append(int(current_result.get_observable_count()))
                mode_index += 1

            result_index += 1

        all_poles_s: CxVec = np.asarray(poles_list, dtype=np.complex128)
        all_residues: CxMat = np.asarray(residue_list, dtype=np.complex128)
        all_energy: Vec = np.asarray(energy_list, dtype=np.float64)
        all_errors: Vec = np.asarray(error_list, dtype=np.float64)
        all_band_low: Vec = np.asarray(band_low_list, dtype=np.float64)
        all_band_high: Vec = np.asarray(band_high_list, dtype=np.float64)
        all_selected_orders: IntVec = np.asarray(selected_order_list, dtype=np.int_)
        all_observable_counts: IntVec = np.asarray(observable_count_list, dtype=np.int_)
        n_all_modes: int = int(all_poles_s.shape[0])
        used_mask: np.ndarray = np.zeros(n_all_modes, dtype=np.bool_)

        merged_poles_list: List[complex] = list()
        merged_residue_list: List[np.ndarray] = list()
        merged_energy_list: List[float] = list()
        merged_error_list: List[float] = list()
        merged_band_low_list: List[float] = list()
        merged_band_high_list: List[float] = list()
        merged_selected_order_list: List[int] = list()
        merged_observable_count_list: List[int] = list()
        reference_index: int = 0

        while reference_index < n_all_modes:
            if not used_mask[reference_index]:
                cluster_indices: List[int] = list()
                cluster_indices.append(reference_index)
                used_mask[reference_index] = True
                candidate_index: int = reference_index + 1

                while candidate_index < n_all_modes:
                    if not used_mask[candidate_index]:
                        frequency_delta_hz: float = abs(
                            float(np.imag(all_poles_s[candidate_index] - all_poles_s[reference_index])) / (2.0 * np.pi)
                        )
                        real_delta: float = abs(float(np.real(all_poles_s[candidate_index] - all_poles_s[reference_index])))

                        if frequency_delta_hz <= era_options.get_frequency_merge_tolerance_hz() and real_delta <= era_options.get_real_part_merge_tolerance():
                            used_mask[candidate_index] = True
                            cluster_indices.append(candidate_index)
                        else:
                            pass
                    else:
                        pass

                    candidate_index += 1

                cluster_array: np.ndarray = np.asarray(cluster_indices, dtype=np.int_)
                cluster_energy: Vec = np.asarray(all_energy[cluster_array], dtype=np.float64)
                weight_sum: float = max(float(np.sum(cluster_energy)), 1e-12)
                cluster_weights: Vec = cluster_energy / weight_sum
                cluster_poles: CxVec = np.asarray(all_poles_s[cluster_array], dtype=np.complex128)
                representative_local_index: int = int(np.argmax(cluster_energy))
                representative_global_index: int = int(cluster_array[representative_local_index])
                fused_pole: complex = complex(np.sum(cluster_weights * cluster_poles))

                merged_poles_list.append(fused_pole)
                merged_residue_list.append(np.asarray(all_residues[representative_global_index, :], dtype=np.complex128))
                merged_energy_list.append(float(np.max(cluster_energy)))
                merged_error_list.append(float(np.min(all_errors[cluster_array])))
                merged_band_low_list.append(float(all_band_low[representative_global_index]))
                merged_band_high_list.append(float(all_band_high[representative_global_index]))
                merged_selected_order_list.append(int(all_selected_orders[representative_global_index]))
                merged_observable_count_list.append(int(all_observable_counts[representative_global_index]))
            else:
                pass

            reference_index += 1

        merged_data: EraMergedModalData = sort_modes_by_frequency_and_damping(
            poles_s=np.asarray(merged_poles_list, dtype=np.complex128),
            residues=np.asarray(merged_residue_list, dtype=np.complex128),
            modal_energy=np.asarray(merged_energy_list, dtype=np.float64),
            reconstruction_errors=np.asarray(merged_error_list, dtype=np.float64),
            band_low_hz=np.asarray(merged_band_low_list, dtype=np.float64),
            band_high_hz=np.asarray(merged_band_high_list, dtype=np.float64),
            selected_orders=np.asarray(merged_selected_order_list, dtype=np.int_),
            observable_count_per_mode=np.asarray(merged_observable_count_list, dtype=np.int_),
        )
    else:
        merged_data = create_empty_merged_modal_data()

    return merged_data


def build_results_from_merged_modal_data(merged_data: EraMergedModalData,
                                         observable_names: List[str]) -> EraMatrixPencilResults:
    """
    Build the public results object from the fused modal data.

    :param merged_data: Fused modal data.
    :param observable_names: Selected observable labels.
    :return: Public results object.
    """
    return EraMatrixPencilResults(
        eigenvalues_s=merged_data.get_poles_s(),
        residues=merged_data.get_residues(),
        modal_energy=merged_data.get_modal_energy(),
        reconstruction_errors=merged_data.get_reconstruction_errors(),
        band_low_hz=merged_data.get_band_low_hz(),
        band_high_hz=merged_data.get_band_high_hz(),
        selected_orders=merged_data.get_selected_orders(),
        observable_count_per_mode=merged_data.get_observable_count_per_mode(),
        observable_names=observable_names,
    )


def extract_matrix_pencil_results_from_data(time_data: Vec,
                                            y_data: Mat,
                                            era_options: EraMatrixPencilOptions,
                                            nominal_frequency_hz: float,
                                            observable_names: List[str] | None = None) -> EraMatrixPencilResults:
    """
    Execute the full EMT frequency-zooming matrix pencil on dense data.

    :param time_data: Raw time vector.
    :param y_data: Raw observation matrix.
    :param era_options: Matrix-pencil options.
    :param nominal_frequency_hz: Nominal grid frequency.
    :param observable_names: Optional channel labels.
    :return: Public EMT modal results.
    """
    dense_signal: Mat = convert_signal_to_2d(np.asarray(y_data, dtype=np.float64))
    dense_time: Vec = np.asarray(time_data, dtype=np.float64)
    n_samples: int = int(dense_signal.shape[0])

    if n_samples == dense_time.shape[0] and n_samples >= 2:
        inferred_step: float = infer_uniform_time_step(dense_time, 0.0)
        uniform_time: Vec
        uniform_signal: Mat
        uniform_time, uniform_signal = resample_to_uniform_time_grid(dense_time, dense_signal, inferred_step)
        selected_signal: Mat
        selected_names: List[str]
        selected_signal, selected_names = select_mimo_observables(
            y_data=uniform_signal,
            observable_names=observable_names,
            maximum_observables=era_options.get_maximum_observables(),
        )
        detrended_signal: Mat = detrend_exponential_dc_offsets(
            time_data=uniform_time,
            y_data=selected_signal,
            use_exponential_detrending=era_options.get_use_exponential_detrending(),
        )
        scaling: EraChannelScaling = compute_channel_scaling(detrended_signal)
        standardized_signal: Mat = standardize_signal_matrix(detrended_signal, scaling)
        effective_time_step: float = infer_uniform_time_step(uniform_time, inferred_step)
        effective_sampling_frequency_hz: float = 1.0 / effective_time_step
        filtered_signal: Mat = apply_notch_filter_matrix(
            y_data=standardized_signal,
            sampling_frequency_hz=effective_sampling_frequency_hz,
            nominal_frequency_hz=nominal_frequency_hz,
            quality_factor=era_options.get_notch_quality_factor(),
            use_notch_filtering=era_options.get_use_notch_filtering(),
            use_zero_phase_filtering=era_options.get_use_zero_phase_filtering(),
        )
        analysis_bands: Tuple[EraMatrixPencilBand, ...] = sanitize_analysis_bands(
            bands=era_options.get_analysis_bands(),
            sampling_frequency_hz=effective_sampling_frequency_hz,
        )
        band_results: List[EraBandResult] = list()
        band_index: int = 0
        n_bands: int = len(analysis_bands)

        # Each band is processed independently so the function is already safe
        # to parallelize in the future without changing any numerical logic.
        while band_index < n_bands:
            current_band: EraMatrixPencilBand = analysis_bands[band_index]
            prepared_band: EraBandSignal = prepare_band_signal(
                time_data=uniform_time,
                y_data=filtered_signal,
                scaling=scaling,
                band=current_band,
                era_options=era_options,
            )
            band_result: EraBandResult = extract_band_modes(prepared_band, era_options)
            band_results.append(band_result)
            band_index += 1

        merged_data: EraMergedModalData = merge_band_results(band_results, era_options)
        results: EraMatrixPencilResults = build_results_from_merged_modal_data(merged_data, selected_names)
    else:
        results = EraMatrixPencilResults(
            eigenvalues_s=build_empty_complex_vector(),
            residues=build_empty_complex_matrix(),
            modal_energy=build_empty_float_vector(),
            reconstruction_errors=build_empty_float_vector(),
            band_low_hz=build_empty_float_vector(),
            band_high_hz=build_empty_float_vector(),
            selected_orders=np.zeros(0, dtype=np.int_),
            observable_count_per_mode=np.zeros(0, dtype=np.int_),
            observable_names=list() if observable_names is None else list(observable_names),
        )

    return results
