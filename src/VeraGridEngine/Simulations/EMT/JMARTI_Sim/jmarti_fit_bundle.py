# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Sequence

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import JMartiModalSamples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import JMartiModeDelayEstimate
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_passivity import JMartiPassivityReport
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import JMartiRationalModeFit


class JMartiFitBundle:
    """
    Aggregated offline JMARTI fitting product ready for runtime conversion.

    The fitting pipeline produces modal preprocessing, per-mode delay estimates,
    per-mode rational fits and optional passivity diagnostics. This object keeps
    those pieces together under one typed interface before the EMT runtime layer
    discretizes and consumes them.
    """

    __slots__ = (
        '_frequency_hz',
        '_line_length_m',
        '_phase_labels',
        '_modal_transform',
        '_modal_transform_inv',
        '_reference_frequency_hz',
        '_decoupling_error_z',
        '_decoupling_error_y',
        '_mode_delays',
        '_yc_fits',
        '_hres_fits',
        '_passivity_report',
    )

    def __init__(self,
                 frequency_hz: np.ndarray,
                 line_length_m: float,
                 phase_labels: tuple[str, ...],
                 modal_transform: np.ndarray,
                 modal_transform_inv: np.ndarray,
                 reference_frequency_hz: float,
                 decoupling_error_z: np.ndarray,
                 decoupling_error_y: np.ndarray,
                 mode_delays: Sequence[JMartiModeDelayEstimate],
                 yc_fits: Sequence[JMartiRationalModeFit],
                 hres_fits: Sequence[JMartiRationalModeFit],
                 passivity_report: JMartiPassivityReport | None) -> None:
        """
        Store one complete offline JMARTI fitting bundle.

        :param frequency_hz: Frequency grid in Hz.
        :param line_length_m: Line length in meters.
        :param phase_labels: Ordered phase labels.
        :param modal_transform: Frozen modal transform.
        :param modal_transform_inv: Inverse frozen modal transform.
        :param reference_frequency_hz: Frequency used to freeze the modal basis.
        :param decoupling_error_z: Off-diagonal Z decoupling errors.
        :param decoupling_error_y: Off-diagonal Y decoupling errors.
        :param mode_delays: Modal delay estimates.
        :param yc_fits: Scalar rational fits of ``Yc`` per mode.
        :param hres_fits: Scalar rational fits of ``Hres`` per mode.
        :param passivity_report: Optional passivity report.
        :return: None.
        """
        self._frequency_hz: np.ndarray = np.asarray(frequency_hz, dtype=np.float64)
        self._line_length_m: float = float(line_length_m)
        self._phase_labels: tuple[str, ...] = phase_labels
        self._modal_transform: np.ndarray = np.asarray(modal_transform, dtype=np.complex128)
        self._modal_transform_inv: np.ndarray = np.asarray(modal_transform_inv, dtype=np.complex128)
        self._reference_frequency_hz: float = float(reference_frequency_hz)
        self._decoupling_error_z: np.ndarray = np.asarray(decoupling_error_z, dtype=np.float64)
        self._decoupling_error_y: np.ndarray = np.asarray(decoupling_error_y, dtype=np.float64)
        self._mode_delays: tuple[JMartiModeDelayEstimate, ...] = tuple(mode_delays)
        self._yc_fits: tuple[JMartiRationalModeFit, ...] = tuple(yc_fits)
        self._hres_fits: tuple[JMartiRationalModeFit, ...] = tuple(hres_fits)
        self._passivity_report: JMartiPassivityReport | None = passivity_report

    def get_frequency_hz(self) -> np.ndarray:
        """
        Return the fitted frequency grid.

        :return: Frequency grid in Hz.
        """
        return self._frequency_hz

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

    def get_reference_frequency_hz(self) -> float:
        """
        Return the frequency used to freeze the modal basis.

        :return: Reference frequency in Hz.
        """
        return self._reference_frequency_hz

    def get_decoupling_error_z(self) -> np.ndarray:
        """
        Return the off-diagonal Z decoupling errors.

        :return: Real-valued Z decoupling error vector.
        """
        return self._decoupling_error_z

    def get_decoupling_error_y(self) -> np.ndarray:
        """
        Return the off-diagonal Y decoupling errors.

        :return: Real-valued Y decoupling error vector.
        """
        return self._decoupling_error_y

    def get_mode_delays(self) -> tuple[JMartiModeDelayEstimate, ...]:
        """
        Return the modal delay estimates.

        :return: Per-mode delay tuple.
        """
        return self._mode_delays

    def get_yc_fits(self) -> tuple[JMartiRationalModeFit, ...]:
        """
        Return the scalar ``Yc`` fits.

        :return: Per-mode ``Yc`` fit tuple.
        """
        return self._yc_fits

    def get_hres_fits(self) -> tuple[JMartiRationalModeFit, ...]:
        """
        Return the scalar ``Hres`` fits.

        :return: Per-mode ``Hres`` fit tuple.
        """
        return self._hres_fits

    def get_passivity_report(self) -> JMartiPassivityReport | None:
        """
        Return the optional passivity report.

        :return: Passivity report or ``None``.
        """
        return self._passivity_report

    def get_mode_count(self) -> int:
        """
        Return the modal order of the fit bundle.

        :return: Number of modes.
        """
        return int(len(self._mode_delays))


def build_jmarti_fit_bundle(modal_samples: JMartiModalSamples,
                            mode_delays: Sequence[JMartiModeDelayEstimate],
                            yc_fits: Sequence[JMartiRationalModeFit],
                            hres_fits: Sequence[JMartiRationalModeFit],
                            passivity_report: JMartiPassivityReport | None = None) -> JMartiFitBundle:
    """
    Build one validated JMARTI fit bundle.

    :param modal_samples: Modal preprocessing output.
    :param mode_delays: Per-mode delay estimates.
    :param yc_fits: Per-mode ``Yc`` rational fits.
    :param hres_fits: Per-mode ``Hres`` rational fits.
    :param passivity_report: Optional passivity report.
    :return: Validated fit bundle.
    :raises ValueError: If the per-mode objects do not align.
    """
    mode_count: int = modal_samples.get_mode_count()
    yc_index: int = 0
    hres_index: int = 0

    if len(mode_delays) == mode_count and len(yc_fits) == mode_count and len(hres_fits) == mode_count:
        pass
    else:
        raise ValueError("JMARTI fit bundle requires exactly one delay, Yc fit and Hres fit per mode")

    yc_index = 0
    while yc_index < mode_count:
        if mode_delays[yc_index].get_mode_index() == yc_index and yc_fits[yc_index].get_mode_index() == yc_index:
            pass
        else:
            raise ValueError("JMARTI delay/Yc fit ordering is inconsistent with the modal indices")

        yc_index += 1

    hres_index = 0
    while hres_index < mode_count:
        if hres_fits[hres_index].get_mode_index() == hres_index:
            pass
        else:
            raise ValueError("JMARTI Hres fit ordering is inconsistent with the modal indices")

        hres_index += 1

    return JMartiFitBundle(
        frequency_hz=modal_samples.get_frequency_hz(),
        line_length_m=modal_samples.get_line_length_m(),
        phase_labels=modal_samples.get_phase_labels(),
        modal_transform=modal_samples.get_modal_transform(),
        modal_transform_inv=modal_samples.get_modal_transform_inv(),
        reference_frequency_hz=modal_samples.get_reference_frequency_hz(),
        decoupling_error_z=modal_samples.get_decoupling_error_z(),
        decoupling_error_y=modal_samples.get_decoupling_error_y(),
        mode_delays=mode_delays,
        yc_fits=yc_fits,
        hres_fits=hres_fits,
        passivity_report=passivity_report,
    )
