# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np
import scipy.linalg as la

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import JMartiFrequencySamples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import build_jmarti_frequency_subset


class JMartiModalSamples:
    """
    Modalized JMARTI frequency samples built from one constant modal transform.

    The first JMARTI implementation in VeraGrid assumes an approximately
    constant modal basis over the fitted band. The object stores that common
    basis and all diagonal modal quantities derived from it.
    """

    __slots__ = (
        '_frequency_hz',
        '_line_length_m',
        '_phase_labels',
        '_modal_transform',
        '_modal_transform_inv',
        '_z_modal',
        '_y_modal',
        '_z_modal_diag',
        '_y_modal_diag',
        '_gamma_modal',
        '_yc_modal',
        '_decoupling_error_z',
        '_decoupling_error_y',
        '_reference_frequency_hz',
    )

    def __init__(self,
                 frequency_hz: np.ndarray,
                 line_length_m: float,
                 phase_labels: tuple[str, ...],
                 modal_transform: np.ndarray,
                 modal_transform_inv: np.ndarray,
                 z_modal: np.ndarray,
                 y_modal: np.ndarray,
                 z_modal_diag: np.ndarray,
                 y_modal_diag: np.ndarray,
                 gamma_modal: np.ndarray,
                 yc_modal: np.ndarray,
                 decoupling_error_z: np.ndarray,
                 decoupling_error_y: np.ndarray,
                 reference_frequency_hz: float) -> None:
        """
        Store one modalized JMARTI sample set.

        :param frequency_hz: Frequency grid in Hz.
        :param line_length_m: Line length in meters.
        :param phase_labels: Ordered phase labels.
        :param modal_transform: Common modal transform.
        :param modal_transform_inv: Inverse of the common modal transform.
        :param z_modal: Projected modal series-impedance matrices.
        :param y_modal: Projected modal shunt-admittance matrices.
        :param z_modal_diag: Diagonal modal impedance samples.
        :param y_modal_diag: Diagonal modal admittance samples.
        :param gamma_modal: Modal propagation constants per unit length.
        :param yc_modal: Modal characteristic admittances.
        :param decoupling_error_z: Off-diagonal Z decoupling errors.
        :param decoupling_error_y: Off-diagonal Y decoupling errors.
        :param reference_frequency_hz: Frequency used to freeze the modal basis.
        :return: None.
        """
        self._frequency_hz: np.ndarray = np.asarray(frequency_hz, dtype=np.float64)
        self._line_length_m: float = float(line_length_m)
        self._phase_labels: tuple[str, ...] = phase_labels
        self._modal_transform: np.ndarray = np.asarray(modal_transform, dtype=np.complex128)
        self._modal_transform_inv: np.ndarray = np.asarray(modal_transform_inv, dtype=np.complex128)
        self._z_modal: np.ndarray = np.asarray(z_modal, dtype=np.complex128)
        self._y_modal: np.ndarray = np.asarray(y_modal, dtype=np.complex128)
        self._z_modal_diag: np.ndarray = np.asarray(z_modal_diag, dtype=np.complex128)
        self._y_modal_diag: np.ndarray = np.asarray(y_modal_diag, dtype=np.complex128)
        self._gamma_modal: np.ndarray = np.asarray(gamma_modal, dtype=np.complex128)
        self._yc_modal: np.ndarray = np.asarray(yc_modal, dtype=np.complex128)
        self._decoupling_error_z: np.ndarray = np.asarray(decoupling_error_z, dtype=np.float64)
        self._decoupling_error_y: np.ndarray = np.asarray(decoupling_error_y, dtype=np.float64)
        self._reference_frequency_hz: float = float(reference_frequency_hz)

    def get_frequency_hz(self) -> np.ndarray:
        """
        Return the modal frequency grid.

        :return: Frequency grid in Hz.
        """
        return self._frequency_hz

    def get_angular_frequency_rad_per_s(self) -> np.ndarray:
        """
        Return the modal angular-frequency grid.

        :return: Angular-frequency grid in rad/s.
        """
        return 2.0 * np.pi * self._frequency_hz

    def get_line_length_m(self) -> float:
        """
        Return the line length in meters.

        :return: Line length in meters.
        """
        return self._line_length_m

    def get_phase_labels(self) -> tuple[str, ...]:
        """
        Return the ordered phase labels.

        :return: Ordered phase-label tuple.
        """
        return self._phase_labels

    def get_modal_transform(self) -> np.ndarray:
        """
        Return the common modal transform.

        :return: Complex modal transform.
        """
        return self._modal_transform

    def get_modal_transform_inv(self) -> np.ndarray:
        """
        Return the inverse common modal transform.

        :return: Inverse modal transform.
        """
        return self._modal_transform_inv

    def get_z_modal(self) -> np.ndarray:
        """
        Return projected modal series-impedance matrices.

        :return: Complex modal impedance tensor.
        """
        return self._z_modal

    def get_y_modal(self) -> np.ndarray:
        """
        Return projected modal shunt-admittance matrices.

        :return: Complex modal admittance tensor.
        """
        return self._y_modal

    def get_z_modal_diag(self) -> np.ndarray:
        """
        Return the diagonal modal impedance samples.

        :return: Complex diagonal modal impedance array.
        """
        return self._z_modal_diag

    def get_y_modal_diag(self) -> np.ndarray:
        """
        Return the diagonal modal admittance samples.

        :return: Complex diagonal modal admittance array.
        """
        return self._y_modal_diag

    def get_gamma_modal(self) -> np.ndarray:
        """
        Return the modal propagation constants per unit length.

        :return: Complex modal propagation constants.
        """
        return self._gamma_modal

    def get_yc_modal(self) -> np.ndarray:
        """
        Return the modal characteristic admittances.

        :return: Complex modal characteristic-admittance array.
        """
        return self._yc_modal

    def get_decoupling_error_z(self) -> np.ndarray:
        """
        Return the off-diagonal Z decoupling errors.

        :return: Real-valued error vector over frequency.
        """
        return self._decoupling_error_z

    def get_decoupling_error_y(self) -> np.ndarray:
        """
        Return the off-diagonal Y decoupling errors.

        :return: Real-valued error vector over frequency.
        """
        return self._decoupling_error_y

    def get_reference_frequency_hz(self) -> float:
        """
        Return the frequency used to freeze the modal basis.

        :return: Reference frequency in Hz.
        """
        return self._reference_frequency_hz

    def get_mode_count(self) -> int:
        """
        Return the number of fitted modes.

        :return: Mode count.
        """
        return int(self._modal_transform.shape[0])


class JMartiModeDelayEstimate:
    """
    Delay estimate of one modal propagation channel.
    """

    __slots__ = (
        '_mode_index',
        '_tau_s',
        '_rms_phase_error_rad',
    )

    def __init__(self, mode_index: int, tau_s: float, rms_phase_error_rad: float) -> None:
        """
        Store one modal delay estimate.

        :param mode_index: Modal channel index.
        :param tau_s: Estimated pure delay in seconds.
        :param rms_phase_error_rad: RMS residual of the affine phase fit.
        :return: None.
        """
        self._mode_index: int = int(mode_index)
        self._tau_s: float = float(tau_s)
        self._rms_phase_error_rad: float = float(rms_phase_error_rad)

    def get_mode_index(self) -> int:
        """
        Return the modal channel index.

        :return: Modal channel index.
        """
        return self._mode_index

    def get_tau_s(self) -> float:
        """
        Return the estimated delay in seconds.

        :return: Delay in seconds.
        """
        return self._tau_s

    def get_rms_phase_error_rad(self) -> float:
        """
        Return the RMS residual of the affine phase fit.

        :return: RMS residual in radians.
        """
        return self._rms_phase_error_rad


def _resolve_reference_frequency_hz(frequency_hz: np.ndarray, options: JMartiFitOptions) -> float:
    """
    Resolve the reference frequency used to freeze the modal basis.

    :param frequency_hz: Available frequency grid in Hz.
    :param options: User-configurable JMARTI fitting options.
    :return: Reference frequency in Hz.
    """
    requested_frequency_hz: float = options.get_reference_frequency_hz()

    if requested_frequency_hz > 0.0:
        return requested_frequency_hz
    else:
        return float(frequency_hz[int(frequency_hz.size // 2)])


def _build_reference_frequency_index(frequency_hz: np.ndarray, reference_frequency_hz: float) -> int:
    """
    Return the sample index used to freeze the modal basis.

    :param frequency_hz: Frequency grid in Hz.
    :param reference_frequency_hz: Requested reference frequency in Hz.
    :return: Frequency-grid index.
    """
    distance_vector: np.ndarray = np.abs(frequency_hz - float(reference_frequency_hz))
    return int(np.argmin(distance_vector))


def _build_reference_modal_transform(z_per_length_at_reference: np.ndarray,
                                     y_per_length_at_reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Build the constant modal transform used by the first JMARTI version.

    :param z_per_length_at_reference: Series impedance matrix at the reference frequency.
    :param y_per_length_at_reference: Shunt admittance matrix at the reference frequency.
    :return: Tuple ``(T0, T0_inv)``.
    :raises ValueError: If the modal transform is singular.
    """
    product_matrix: np.ndarray = z_per_length_at_reference @ y_per_length_at_reference
    eigenvalues: np.ndarray
    eigenvectors: np.ndarray
    order_index: np.ndarray
    modal_transform: np.ndarray
    modal_transform_inv: np.ndarray

    # Stage 1: diagonalize the per-unit-length product operator. In the canonical
    # JMARTI workflow this basis approximates the frequency-independent modal frame.
    eigenvalues, eigenvectors = la.eig(product_matrix)

    # Stage 2: impose a deterministic mode ordering so every later fitting stage
    # sees stable mode indices across runs and across test environments.
    order_index = np.argsort(np.real(eigenvalues))
    modal_transform = eigenvectors[:, order_index]

    try:
        modal_transform_inv = la.inv(modal_transform)
    except la.LinAlgError as exc:
        raise ValueError("JMARTI modal transform is singular at the reference frequency") from exc

    return modal_transform, modal_transform_inv


def _compute_modal_decoupling_errors(modal_tensor: np.ndarray) -> np.ndarray:
    """
    Compute one normalized off-diagonal error for every frequency sample.

    :param modal_tensor: Complex modal matrix tensor with shape ``(nf, nm, nm)``.
    :return: Vector of off-diagonal Frobenius ratios.
    """
    total_energy: np.ndarray = np.sum(np.abs(modal_tensor) ** 2, axis=(1, 2))
    diagonal_energy: np.ndarray = np.sum(np.abs(np.diagonal(modal_tensor, axis1=1, axis2=2)) ** 2, axis=1)
    off_diagonal_energy: np.ndarray = np.maximum(total_energy - diagonal_energy, 0.0)
    decoupling_error: np.ndarray = np.zeros(modal_tensor.shape[0], dtype=np.float64)
    valid_mask: np.ndarray = total_energy > 0.0

    if np.any(valid_mask):
        decoupling_error[valid_mask] = np.sqrt(off_diagonal_energy[valid_mask] / total_energy[valid_mask])
    else:
        pass

    return decoupling_error


def _apply_jmarti_frequency_window(samples: JMartiFrequencySamples,
                                   options: JMartiFitOptions) -> JMartiFrequencySamples:
    """
    Apply the optional user-selected frequency exploration window.

    :param samples: Full JMARTI frequency sample set.
    :param options: User-configurable JMARTI fitting options.
    :return: Possibly windowed sample set.
    """
    if options.get_use_frequency_exploration_window():
        return build_jmarti_frequency_subset(
            samples=samples,
            low_hz=options.get_exploration_low_hz(),
            high_hz=options.get_exploration_high_hz(),
        )
    else:
        return samples


def build_jmarti_modal_samples(samples: JMartiFrequencySamples,
                               options: JMartiFitOptions | None = None) -> JMartiModalSamples:
    """
    Build modal JMARTI samples from one frequency-domain line dataset.

    The first JMARTI implementation freezes one common modal basis at a single
    reference frequency and reuses it across the whole fitted band. This is the
    standard pragmatic starting point before moving to a fully frequency-varying
    modal transform.

    :param samples: Frequency-domain line dataset.
    :param options: Optional user-configurable JMARTI fitting options.
    :return: Modalized sample set.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    working_samples: JMartiFrequencySamples = _apply_jmarti_frequency_window(samples, resolved_options)
    frequency_hz: np.ndarray = working_samples.get_frequency_hz()
    z_per_length: np.ndarray = working_samples.get_z_per_length()
    y_per_length: np.ndarray = working_samples.get_y_per_length()
    line_length_m: float = working_samples.get_line_length_m()
    phase_labels: tuple[str, ...] = working_samples.get_phase_labels()
    reference_frequency_hz: float = _resolve_reference_frequency_hz(frequency_hz, resolved_options)
    reference_index: int = _build_reference_frequency_index(frequency_hz, reference_frequency_hz)
    sample_count: int = working_samples.get_frequency_count()
    mode_count: int = working_samples.get_phase_count()
    modal_transform: np.ndarray
    modal_transform_inv: np.ndarray

    if sample_count >= resolved_options.get_minimum_frequency_samples():
        pass
    else:
        raise ValueError(
            "JMARTI modal processing requires at least "
            f"{resolved_options.get_minimum_frequency_samples()} frequency samples"
        )

    modal_transform, modal_transform_inv = _build_reference_modal_transform(
        z_per_length_at_reference=z_per_length[reference_index, :, :],
        y_per_length_at_reference=y_per_length[reference_index, :, :],
    )

    # Stage 1: project every frequency sample into the frozen modal basis using
    # tensor contractions so the whole band is transformed with one vectorized pass.
    z_modal: np.ndarray = np.einsum(
        'ij,fjk,kl->fil',
        modal_transform_inv,
        z_per_length,
        modal_transform,
        optimize=True,
    )
    y_modal: np.ndarray = np.einsum(
        'ij,fjk,kl->fil',
        modal_transform_inv,
        y_per_length,
        modal_transform,
        optimize=True,
    )
    z_modal_diag: np.ndarray = np.diagonal(z_modal, axis1=1, axis2=2).copy()
    y_modal_diag: np.ndarray = np.diagonal(y_modal, axis1=1, axis2=2).copy()

    # Stage 2: derive the scalar modal quantities that the canonical JMARTI
    # formulation fits independently per mode.
    gamma_modal: np.ndarray = np.sqrt(z_modal_diag * y_modal_diag)
    yc_modal: np.ndarray = np.sqrt(y_modal_diag / z_modal_diag)

    # Stage 3: quantify how far the common modal basis is from exact diagonalization.
    decoupling_error_z: np.ndarray = _compute_modal_decoupling_errors(z_modal)
    decoupling_error_y: np.ndarray = _compute_modal_decoupling_errors(y_modal)

    return JMartiModalSamples(
        frequency_hz=frequency_hz,
        line_length_m=line_length_m,
        phase_labels=phase_labels,
        modal_transform=modal_transform,
        modal_transform_inv=modal_transform_inv,
        z_modal=z_modal,
        y_modal=y_modal,
        z_modal_diag=z_modal_diag,
        y_modal_diag=y_modal_diag,
        gamma_modal=gamma_modal,
        yc_modal=yc_modal,
        decoupling_error_z=decoupling_error_z,
        decoupling_error_y=decoupling_error_y,
        reference_frequency_hz=reference_frequency_hz,
    )


def estimate_jmarti_mode_delays(modal_samples: JMartiModalSamples,
                                options: JMartiFitOptions | None = None) -> list[JMartiModeDelayEstimate]:
    """
    Estimate one pure propagation delay for each JMARTI mode.

    The pure delay is extracted from the modal propagation phase
    ``beta(omega) * length`` through one affine fit in angular frequency. The
    residual phase error indicates how much non-ideal frequency dispersion is
    left for the rational residual propagation fit.

    :param modal_samples: Modalized JMARTI sample set.
    :param options: Optional user-configurable JMARTI fitting options.
    :return: Delay estimates for every modal channel.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    frequency_hz: np.ndarray = modal_samples.get_frequency_hz()
    angular_frequency: np.ndarray = modal_samples.get_angular_frequency_rad_per_s()
    gamma_modal: np.ndarray = modal_samples.get_gamma_modal()
    line_length_m: float = modal_samples.get_line_length_m()
    mode_count: int = modal_samples.get_mode_count()
    selected_mask: np.ndarray = np.ones(frequency_hz.size, dtype=bool)
    delay_estimates: list[JMartiModeDelayEstimate] = list()
    mode_index: int
    phase_data: np.ndarray
    fit_coefficients: np.ndarray
    fitted_phase: np.ndarray
    phase_error: np.ndarray
    tau_s: float
    rms_phase_error_rad: float

    # Stage 1: select the frequency band used to estimate the affine delay term.
    if resolved_options.get_use_delay_fit_window():
        selected_mask = (
            (frequency_hz >= resolved_options.get_delay_fit_low_hz())
            & (frequency_hz <= resolved_options.get_delay_fit_high_hz())
        )
    else:
        pass

    # Stage 2: fall back to the whole band if the requested window is too small
    # to sustain a meaningful slope estimate.
    if int(np.count_nonzero(selected_mask)) >= 2:
        pass
    else:
        selected_mask = np.ones(frequency_hz.size, dtype=bool)

    mode_index = 0
    while mode_index < mode_count:
        # The propagation phase of one mode is ``beta * length``. A linear fit of
        # that quantity versus angular frequency returns the pure modal delay.
        phase_data = np.imag(gamma_modal[:, mode_index]) * line_length_m
        fit_coefficients = np.polyfit(angular_frequency[selected_mask], phase_data[selected_mask], deg=1)
        fitted_phase = fit_coefficients[0] * angular_frequency[selected_mask] + fit_coefficients[1]
        phase_error = phase_data[selected_mask] - fitted_phase
        tau_s = float(fit_coefficients[0])
        rms_phase_error_rad = float(np.sqrt(np.mean(phase_error * phase_error)))
        delay_estimates.append(
            JMartiModeDelayEstimate(
                mode_index=mode_index,
                tau_s=tau_s,
                rms_phase_error_rad=rms_phase_error_rad,
            )
        )
        mode_index += 1

    return delay_estimates
