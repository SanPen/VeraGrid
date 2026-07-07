# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_bundle import JMartiFitBundle


class JMartiModeRuntimeData:
    """
    Discrete-time runtime coefficients of one scalar JMARTI modal channel.

    The EMT runtime will later consume these coefficients directly instead of
    re-discretizing every pole on the fly. This keeps the time-stepping loop as
    lean as possible.
    """

    __slots__ = (
        '_mode_index',
        '_tau_s',
        '_delay_step_count',
        '_residual_delay_s',
        '_yc_poles_s',
        '_yc_residues',
        '_yc_constant_term',
        '_yc_proportional_term',
        '_hres_poles_s',
        '_hres_residues',
        '_hres_constant_term',
        '_hres_proportional_term',
        '_yc_alpha',
        '_yc_beta',
        '_hres_alpha',
        '_hres_beta',
    )

    def __init__(self,
                 mode_index: int,
                 tau_s: float,
                 delay_step_count: int,
                 residual_delay_s: float,
                 yc_poles_s: np.ndarray,
                 yc_residues: np.ndarray,
                 yc_constant_term: complex,
                 yc_proportional_term: complex,
                 hres_poles_s: np.ndarray,
                 hres_residues: np.ndarray,
                 hres_constant_term: complex,
                 hres_proportional_term: complex,
                 yc_alpha: np.ndarray,
                 yc_beta: np.ndarray,
                 hres_alpha: np.ndarray,
                 hres_beta: np.ndarray) -> None:
        """
        Store one discretized modal runtime record.

        :param mode_index: Modal channel index.
        :param tau_s: Estimated pure delay in seconds.
        :param delay_step_count: Integer delay in EMT steps.
        :param residual_delay_s: Remaining sub-step delay in seconds.
        :param yc_poles_s: Continuous-time poles of ``Yc``.
        :param yc_residues: Residues of ``Yc``.
        :param yc_constant_term: Constant term of ``Yc``.
        :param yc_proportional_term: Proportional term of ``Yc``.
        :param hres_poles_s: Continuous-time poles of ``Hres``.
        :param hres_residues: Residues of ``Hres``.
        :param hres_constant_term: Constant term of ``Hres``.
        :param hres_proportional_term: Proportional term of ``Hres``.
        :param yc_alpha: Exact discrete state-transition multipliers of ``Yc``.
        :param yc_beta: Exact discrete input gains of ``Yc``.
        :param hres_alpha: Exact discrete state-transition multipliers of ``Hres``.
        :param hres_beta: Exact discrete input gains of ``Hres``.
        :return: None.
        """
        self._mode_index: int = int(mode_index)
        self._tau_s: float = float(tau_s)
        self._delay_step_count: int = int(delay_step_count)
        self._residual_delay_s: float = float(residual_delay_s)
        self._yc_poles_s: np.ndarray = np.asarray(yc_poles_s, dtype=np.complex128)
        self._yc_residues: np.ndarray = np.asarray(yc_residues, dtype=np.complex128)
        self._yc_constant_term: complex = complex(yc_constant_term)
        self._yc_proportional_term: complex = complex(yc_proportional_term)
        self._hres_poles_s: np.ndarray = np.asarray(hres_poles_s, dtype=np.complex128)
        self._hres_residues: np.ndarray = np.asarray(hres_residues, dtype=np.complex128)
        self._hres_constant_term: complex = complex(hres_constant_term)
        self._hres_proportional_term: complex = complex(hres_proportional_term)
        self._yc_alpha: np.ndarray = np.asarray(yc_alpha, dtype=np.complex128)
        self._yc_beta: np.ndarray = np.asarray(yc_beta, dtype=np.complex128)
        self._hres_alpha: np.ndarray = np.asarray(hres_alpha, dtype=np.complex128)
        self._hres_beta: np.ndarray = np.asarray(hres_beta, dtype=np.complex128)

    def get_mode_index(self) -> int:
        """
        Return the modal channel index.

        :return: Modal channel index.
        """
        return self._mode_index

    def get_tau_s(self) -> float:
        """
        Return the pure delay in seconds.

        :return: Pure delay in seconds.
        """
        return self._tau_s

    def get_delay_step_count(self) -> int:
        """
        Return the integer delay in EMT steps.

        :return: Integer delay in EMT steps.
        """
        return self._delay_step_count

    def get_residual_delay_s(self) -> float:
        """
        Return the unresolved sub-step delay in seconds.

        :return: Residual delay in seconds.
        """
        return self._residual_delay_s

    def get_yc_poles_s(self) -> np.ndarray:
        """
        Return the continuous-time poles of ``Yc``.

        :return: Complex pole vector of ``Yc``.
        """
        return self._yc_poles_s

    def get_yc_residues(self) -> np.ndarray:
        """
        Return the residues of ``Yc``.

        :return: Complex residue vector of ``Yc``.
        """
        return self._yc_residues

    def get_yc_constant_term(self) -> complex:
        """
        Return the constant term of ``Yc``.

        :return: Complex constant term of ``Yc``.
        """
        return self._yc_constant_term

    def get_yc_proportional_term(self) -> complex:
        """
        Return the proportional term of ``Yc``.

        :return: Complex proportional term of ``Yc``.
        """
        return self._yc_proportional_term

    def get_hres_poles_s(self) -> np.ndarray:
        """
        Return the continuous-time poles of ``Hres``.

        :return: Complex pole vector of ``Hres``.
        """
        return self._hres_poles_s

    def get_hres_residues(self) -> np.ndarray:
        """
        Return the residues of ``Hres``.

        :return: Complex residue vector of ``Hres``.
        """
        return self._hres_residues

    def get_hres_constant_term(self) -> complex:
        """
        Return the constant term of ``Hres``.

        :return: Complex constant term of ``Hres``.
        """
        return self._hres_constant_term

    def get_hres_proportional_term(self) -> complex:
        """
        Return the proportional term of ``Hres``.

        :return: Complex proportional term of ``Hres``.
        """
        return self._hres_proportional_term

    def get_yc_alpha(self) -> np.ndarray:
        """
        Return the exact discrete state-transition multipliers of ``Yc``.

        :return: Complex transition multipliers.
        """
        return self._yc_alpha

    def get_yc_beta(self) -> np.ndarray:
        """
        Return the exact discrete input gains of ``Yc``.

        :return: Complex input gains.
        """
        return self._yc_beta

    def get_hres_alpha(self) -> np.ndarray:
        """
        Return the exact discrete state-transition multipliers of ``Hres``.

        :return: Complex transition multipliers.
        """
        return self._hres_alpha

    def get_hres_beta(self) -> np.ndarray:
        """
        Return the exact discrete input gains of ``Hres``.

        :return: Complex input gains.
        """
        return self._hres_beta


class JMartiRuntimeData:
    """
    Runtime-ready discrete JMARTI data built from one offline fit bundle.
    """

    __slots__ = (
        '_time_step_s',
        '_line_length_m',
        '_phase_labels',
        '_modal_transform',
        '_modal_transform_inv',
        '_reference_frequency_hz',
        '_mode_data',
    )

    def __init__(self,
                 time_step_s: float,
                 line_length_m: float,
                 phase_labels: tuple[str, ...],
                 modal_transform: np.ndarray,
                 modal_transform_inv: np.ndarray,
                 reference_frequency_hz: float,
                 mode_data: tuple[JMartiModeRuntimeData, ...]) -> None:
        """
        Store one runtime-ready JMARTI dataset.

        :param time_step_s: EMT time step in seconds.
        :param line_length_m: Line length in meters.
        :param phase_labels: Ordered phase labels.
        :param modal_transform: Frozen modal transform.
        :param modal_transform_inv: Inverse frozen modal transform.
        :param reference_frequency_hz: Frequency used to freeze the modal basis.
        :param mode_data: Discrete modal runtime data.
        :return: None.
        """
        self._time_step_s: float = float(time_step_s)
        self._line_length_m: float = float(line_length_m)
        self._phase_labels: tuple[str, ...] = phase_labels
        self._modal_transform: np.ndarray = np.asarray(modal_transform, dtype=np.complex128)
        self._modal_transform_inv: np.ndarray = np.asarray(modal_transform_inv, dtype=np.complex128)
        self._reference_frequency_hz: float = float(reference_frequency_hz)
        self._mode_data: tuple[JMartiModeRuntimeData, ...] = mode_data

    def get_time_step_s(self) -> float:
        """
        Return the EMT time step in seconds.

        :return: EMT time step in seconds.
        """
        return self._time_step_s

    def get_mode_data(self) -> tuple[JMartiModeRuntimeData, ...]:
        """
        Return the discrete modal runtime records.

        :return: Modal runtime tuple.
        """
        return self._mode_data

    def get_modal_transform(self) -> np.ndarray:
        """
        Return the frozen modal transform.

        :return: Complex modal transform.
        """
        return self._modal_transform

    def get_modal_transform_inv(self) -> np.ndarray:
        """
        Return the inverse frozen modal transform.

        :return: Inverse modal transform.
        """
        return self._modal_transform_inv

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

    def get_reference_frequency_hz(self) -> float:
        """
        Return the modal-reference frequency.

        :return: Reference frequency in Hz.
        """
        return self._reference_frequency_hz

    def get_mode_count(self) -> int:
        """
        Return the number of modes.

        :return: Number of modes.
        """
        return int(len(self._mode_data))


def _build_exact_discrete_coefficients(poles_s: np.ndarray,
                                       residues: np.ndarray,
                                       time_step_s: float) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert one first-order pole-residue family into exact discrete coefficients.

    :param poles_s: Continuous-time poles.
    :param residues: Continuous-time residues used as input gains.
    :param time_step_s: EMT time step in seconds.
    :return: Tuple ``(alpha, beta)``.
    """
    alpha: np.ndarray = np.exp(poles_s * time_step_s)
    beta: np.ndarray = np.zeros(poles_s.size, dtype=np.complex128)
    non_zero_mask: np.ndarray = np.abs(poles_s) > 1.0e-20

    if np.any(non_zero_mask):
        beta[non_zero_mask] = residues[non_zero_mask] * (alpha[non_zero_mask] - 1.0) / poles_s[non_zero_mask]
    else:
        pass

    if np.any(~non_zero_mask):
        beta[~non_zero_mask] = residues[~non_zero_mask] * time_step_s
    else:
        pass

    return alpha, beta


def _build_delay_step_decomposition(tau_s: float, time_step_s: float) -> tuple[int, float]:
    """
    Split one pure delay into an integer number of EMT steps and a residual part.

    :param tau_s: Pure delay in seconds.
    :param time_step_s: EMT time step in seconds.
    :return: Tuple ``(delay_step_count, residual_delay_s)``.
    """
    delay_step_count: int = int(np.floor(float(tau_s) / float(time_step_s)))
    residual_delay_s: float = float(tau_s - delay_step_count * time_step_s)
    return delay_step_count, residual_delay_s


def build_jmarti_runtime_data(fit_bundle: JMartiFitBundle,
                              time_step_s: float) -> JMartiRuntimeData:
    """
    Build runtime-ready discrete JMARTI coefficients from one offline fit bundle.

    :param fit_bundle: Offline JMARTI fit bundle.
    :param time_step_s: EMT time step in seconds.
    :return: Runtime-ready JMARTI dataset.
    :raises ValueError: If the time step is not strictly positive.
    """
    sanitized_time_step_s: float = float(time_step_s)
    mode_count: int = fit_bundle.get_mode_count()
    mode_data: list[JMartiModeRuntimeData] = list()
    mode_index: int = 0
    mode_delay = None
    yc_fit = None
    hres_fit = None
    delay_step_count: int
    residual_delay_s: float
    yc_alpha: np.ndarray
    yc_beta: np.ndarray
    hres_alpha: np.ndarray
    hres_beta: np.ndarray

    if sanitized_time_step_s > 0.0:
        pass
    else:
        raise ValueError("JMARTI runtime conversion requires a strictly positive EMT time step")

    while mode_index < mode_count:
        mode_delay = fit_bundle.get_mode_delays()[mode_index]
        yc_fit = fit_bundle.get_yc_fits()[mode_index]
        hres_fit = fit_bundle.get_hres_fits()[mode_index]

        if abs(yc_fit.get_proportional_term()) <= 1.0e-14:
            pass
        else:
            raise ValueError("The first JMARTI EMT runtime does not support a proportional term in Yc")

        if abs(hres_fit.get_proportional_term()) <= 1.0e-14:
            pass
        else:
            raise ValueError("The first JMARTI EMT runtime does not support a proportional term in Hres")

        delay_step_count, residual_delay_s = _build_delay_step_decomposition(
            tau_s=mode_delay.get_tau_s(),
            time_step_s=sanitized_time_step_s,
        )
        yc_alpha, yc_beta = _build_exact_discrete_coefficients(
            poles_s=yc_fit.get_poles_s(),
            residues=yc_fit.get_residues(),
            time_step_s=sanitized_time_step_s,
        )
        hres_alpha, hres_beta = _build_exact_discrete_coefficients(
            poles_s=hres_fit.get_poles_s(),
            residues=hres_fit.get_residues(),
            time_step_s=sanitized_time_step_s,
        )
        mode_data.append(
            JMartiModeRuntimeData(
                mode_index=mode_index,
                tau_s=mode_delay.get_tau_s(),
                delay_step_count=delay_step_count,
                residual_delay_s=residual_delay_s,
                yc_poles_s=yc_fit.get_poles_s(),
                yc_residues=yc_fit.get_residues(),
                yc_constant_term=yc_fit.get_constant_term(),
                yc_proportional_term=yc_fit.get_proportional_term(),
                hres_poles_s=hres_fit.get_poles_s(),
                hres_residues=hres_fit.get_residues(),
                hres_constant_term=hres_fit.get_constant_term(),
                hres_proportional_term=hres_fit.get_proportional_term(),
                yc_alpha=yc_alpha,
                yc_beta=yc_beta,
                hres_alpha=hres_alpha,
                hres_beta=hres_beta,
            )
        )
        mode_index += 1

    return JMartiRuntimeData(
        time_step_s=sanitized_time_step_s,
        line_length_m=fit_bundle.get_line_length_m(),
        phase_labels=fit_bundle.get_phase_labels(),
        modal_transform=fit_bundle.get_modal_transform(),
        modal_transform_inv=fit_bundle.get_modal_transform_inv(),
        reference_frequency_hz=fit_bundle.get_reference_frequency_hz(),
        mode_data=tuple(mode_data),
    )
