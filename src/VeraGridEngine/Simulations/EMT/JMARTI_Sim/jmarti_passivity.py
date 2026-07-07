# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Sequence

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import JMartiRationalModeFit
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import evaluate_jmarti_rational_mode_fit


class JMartiModePassivityReport:
    """
    Passivity-like and boundedness metrics for one scalar JMARTI mode.

    The first JMARTI implementation treats the modal channels independently. For
    that reason the physical admissibility checks are also scalar per mode:
    ``Re(Yc)`` must remain non-negative within tolerance and ``|Hres|`` must not
    exceed one beyond the configured slack.
    """

    __slots__ = (
        '_mode_index',
        '_target_name',
        '_minimum_real_part',
        '_maximum_gain',
        '_minimum_real_frequency_hz',
        '_maximum_gain_frequency_hz',
        '_passes_real_part_check',
        '_passes_gain_check',
    )

    def __init__(self,
                 mode_index: int,
                 target_name: str,
                 minimum_real_part: float,
                 maximum_gain: float,
                 minimum_real_frequency_hz: float,
                 maximum_gain_frequency_hz: float,
                 passes_real_part_check: bool,
                 passes_gain_check: bool) -> None:
        """
        Store one scalar passivity/boundedness report.

        :param mode_index: Modal channel index.
        :param target_name: Scalar target name.
        :param minimum_real_part: Minimum sampled real part.
        :param maximum_gain: Maximum sampled magnitude.
        :param minimum_real_frequency_hz: Frequency where the minimum real part occurs.
        :param maximum_gain_frequency_hz: Frequency where the maximum gain occurs.
        :param passes_real_part_check: Whether the real-part test passes.
        :param passes_gain_check: Whether the gain test passes.
        :return: None.
        """
        self._mode_index: int = int(mode_index)
        self._target_name: str = str(target_name)
        self._minimum_real_part: float = float(minimum_real_part)
        self._maximum_gain: float = float(maximum_gain)
        self._minimum_real_frequency_hz: float = float(minimum_real_frequency_hz)
        self._maximum_gain_frequency_hz: float = float(maximum_gain_frequency_hz)
        self._passes_real_part_check: bool = bool(passes_real_part_check)
        self._passes_gain_check: bool = bool(passes_gain_check)

    def get_mode_index(self) -> int:
        """
        Return the modal channel index.

        :return: Modal channel index.
        """
        return self._mode_index

    def get_target_name(self) -> str:
        """
        Return the scalar target name.

        :return: Scalar target name.
        """
        return self._target_name

    def get_minimum_real_part(self) -> float:
        """
        Return the minimum sampled real part.

        :return: Minimum sampled real part.
        """
        return self._minimum_real_part

    def get_maximum_gain(self) -> float:
        """
        Return the maximum sampled magnitude.

        :return: Maximum sampled magnitude.
        """
        return self._maximum_gain

    def get_minimum_real_frequency_hz(self) -> float:
        """
        Return the frequency where the minimum real part occurs.

        :return: Frequency in Hz.
        """
        return self._minimum_real_frequency_hz

    def get_maximum_gain_frequency_hz(self) -> float:
        """
        Return the frequency where the maximum magnitude occurs.

        :return: Frequency in Hz.
        """
        return self._maximum_gain_frequency_hz

    def get_passes_real_part_check(self) -> bool:
        """
        Return whether the real-part admissibility test passes.

        :return: Boolean state.
        """
        return self._passes_real_part_check

    def get_passes_gain_check(self) -> bool:
        """
        Return whether the gain admissibility test passes.

        :return: Boolean state.
        """
        return self._passes_gain_check


class JMartiPassivityReport:
    """
    Aggregate passivity-like report for a set of scalar JMARTI fits.
    """

    __slots__ = (
        '_frequency_hz',
        '_mode_reports',
    )

    def __init__(self, frequency_hz: np.ndarray, mode_reports: Sequence[JMartiModePassivityReport]) -> None:
        """
        Store one aggregate passivity report.

        :param frequency_hz: Dense frequency grid used for the checks.
        :param mode_reports: Per-mode admissibility reports.
        :return: None.
        """
        self._frequency_hz: np.ndarray = np.asarray(frequency_hz, dtype=np.float64)
        self._mode_reports: tuple[JMartiModePassivityReport, ...] = tuple(mode_reports)

    def get_frequency_hz(self) -> np.ndarray:
        """
        Return the dense frequency grid used for the checks.

        :return: Dense frequency grid in Hz.
        """
        return self._frequency_hz

    def get_mode_reports(self) -> tuple[JMartiModePassivityReport, ...]:
        """
        Return the per-mode reports.

        :return: Per-mode report tuple.
        """
        return self._mode_reports

    def get_all_checks_pass(self) -> bool:
        """
        Return whether every mode passes its admissibility checks.

        :return: Boolean global status.
        """
        report_index: int = 0

        while report_index < len(self._mode_reports):
            report = self._mode_reports[report_index]

            if report.get_passes_real_part_check() and report.get_passes_gain_check():
                pass
            else:
                return False

            report_index += 1

        return True


def build_jmarti_passivity_frequency_grid(low_hz: float,
                                          high_hz: float,
                                          sample_count: int) -> np.ndarray:
    """
    Build one dense frequency grid for passivity checks.

    :param low_hz: Lower frequency in Hz.
    :param high_hz: Upper frequency in Hz.
    :param sample_count: Number of samples requested by the user.
    :return: Dense logarithmic or affine frequency grid.
    """
    if low_hz > 0.0:
        return np.logspace(np.log10(low_hz), np.log10(high_hz), sample_count, dtype=np.float64)
    else:
        return np.linspace(low_hz, high_hz, sample_count, dtype=np.float64)


def evaluate_jmarti_mode_passivity(fit: JMartiRationalModeFit,
                                   frequency_hz: Sequence[float],
                                   options: JMartiFitOptions | None = None) -> JMartiModePassivityReport:
    """
    Evaluate one scalar JMARTI mode on a dense frequency grid.

    ``Yc`` is checked through its minimum real part, while propagation-like
    targets such as ``Hres`` are checked through their maximum gain.

    :param fit: Scalar rational fit.
    :param frequency_hz: Dense frequency grid in Hz.
    :param options: Optional user-configurable JMARTI fitting options.
    :return: Scalar passivity/boundedness report.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    response_values: np.ndarray = evaluate_jmarti_rational_mode_fit(fit, frequency_hz)
    real_part: np.ndarray = np.real(response_values)
    gain: np.ndarray = np.abs(response_values)
    minimum_real_index: int = int(np.argmin(real_part))
    maximum_gain_index: int = int(np.argmax(gain))
    minimum_real_part: float = float(real_part[minimum_real_index])
    maximum_gain: float = float(gain[maximum_gain_index])
    passes_real_part_check: bool = minimum_real_part >= -resolved_options.get_passivity_minimum_real_yc_tolerance()
    passes_gain_check: bool = maximum_gain <= 1.0 + resolved_options.get_passivity_maximum_hres_gain_tolerance()

    if fit.get_target_name() == 'Yc':
        passes_gain_check = True
    else:
        pass

    if fit.get_target_name() == 'Hres':
        passes_real_part_check = True
    else:
        pass

    return JMartiModePassivityReport(
        mode_index=fit.get_mode_index(),
        target_name=fit.get_target_name(),
        minimum_real_part=minimum_real_part,
        maximum_gain=maximum_gain,
        minimum_real_frequency_hz=float(np.asarray(frequency_hz, dtype=np.float64)[minimum_real_index]),
        maximum_gain_frequency_hz=float(np.asarray(frequency_hz, dtype=np.float64)[maximum_gain_index]),
        passes_real_part_check=passes_real_part_check,
        passes_gain_check=passes_gain_check,
    )


def evaluate_jmarti_passivity_report(fits: Sequence[JMartiRationalModeFit],
                                     low_hz: float,
                                     high_hz: float,
                                     options: JMartiFitOptions | None = None) -> JMartiPassivityReport:
    """
    Evaluate passivity-like metrics for a set of scalar JMARTI fits.

    :param fits: Scalar rational fits to inspect.
    :param low_hz: Lower frequency of the dense check grid.
    :param high_hz: Upper frequency of the dense check grid.
    :param options: Optional user-configurable JMARTI fitting options.
    :return: Aggregate passivity report.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    frequency_hz: np.ndarray = build_jmarti_passivity_frequency_grid(
        low_hz=float(low_hz),
        high_hz=float(high_hz),
        sample_count=resolved_options.get_passivity_frequency_sample_count(),
    )
    reports: list[JMartiModePassivityReport] = list()
    fit_index: int = 0

    while fit_index < len(fits):
        reports.append(
            evaluate_jmarti_mode_passivity(
                fit=fits[fit_index],
                frequency_hz=frequency_hz,
                options=resolved_options,
            )
        )
        fit_index += 1

    return JMartiPassivityReport(frequency_hz=frequency_hz, mode_reports=reports)
