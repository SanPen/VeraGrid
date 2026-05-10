# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Sequence

import numpy as np


class JMartiFrequencySamples:
    """
    Typed container holding frequency-domain line samples for one JMARTI fit.

    The fitting workflow starts from sampled multiconductor series impedance and
    shunt admittance matrices. The container validates all structural
    assumptions once so every later fitting stage can rely on a coherent input.
    """

    __slots__ = (
        "_frequency_hz",
        "_z_per_length",
        "_y_per_length",
        "_line_length_m",
        "_phase_labels",
    )

    def __init__(self,
                 frequency_hz: Sequence[float],
                 z_per_length: np.ndarray,
                 y_per_length: np.ndarray,
                 line_length_m: float,
                 phase_labels: Sequence[str]) -> None:
        """
        Build one validated JMARTI frequency-sample container.

        :param frequency_hz: Strictly increasing frequency samples in Hz.
        :param z_per_length: Series impedance matrices with shape ``(nf, np, np)``.
        :param y_per_length: Shunt admittance matrices with shape ``(nf, np, np)``.
        :param line_length_m: Physical line length in meters.
        :param phase_labels: Ordered phase labels associated with the matrices.
        :return: None.
        """
        self._frequency_hz: np.ndarray = np.asarray(frequency_hz, dtype=np.float64)
        self._z_per_length: np.ndarray = np.asarray(z_per_length, dtype=np.complex128)
        self._y_per_length: np.ndarray = np.asarray(y_per_length, dtype=np.complex128)
        self._line_length_m: float = float(line_length_m)
        self._phase_labels: tuple[str, ...] = tuple(str(label) for label in phase_labels)

        validate_jmarti_frequency_samples(self)

    def get_frequency_hz(self) -> np.ndarray:
        """
        Return the sampled frequency vector.

        :return: Frequency vector in Hz.
        """
        return self._frequency_hz

    def get_angular_frequency_rad_per_s(self) -> np.ndarray:
        """
        Return the sampled angular-frequency vector.

        :return: Angular-frequency vector in rad/s.
        """
        return 2.0 * np.pi * self._frequency_hz

    def get_z_per_length(self) -> np.ndarray:
        """
        Return the sampled series impedance matrices.

        :return: Complex impedance tensor with shape ``(nf, np, np)``.
        """
        return self._z_per_length

    def get_y_per_length(self) -> np.ndarray:
        """
        Return the sampled shunt admittance matrices.

        :return: Complex admittance tensor with shape ``(nf, np, np)``.
        """
        return self._y_per_length

    def get_line_length_m(self) -> float:
        """
        Return the physical line length in meters.

        :return: Line length in meters.
        """
        return self._line_length_m

    def get_phase_labels(self) -> tuple[str, ...]:
        """
        Return the ordered phase labels.

        :return: Ordered phase-label tuple.
        """
        return self._phase_labels

    def get_frequency_count(self) -> int:
        """
        Return the number of sampled frequencies.

        :return: Number of frequency samples.
        """
        return int(self._frequency_hz.size)

    def get_phase_count(self) -> int:
        """
        Return the number of conductors or phases in the sample set.

        :return: Matrix dimension.
        """
        return int(len(self._phase_labels))


def validate_jmarti_frequency_samples(samples: JMartiFrequencySamples) -> None:
    """
    Validate one JMARTI frequency-sample container.

    :param samples: Frequency-sample container to validate.
    :return: None.
    :raises ValueError: If the sample set is structurally inconsistent.
    """
    frequency_hz: np.ndarray = samples.get_frequency_hz()
    z_per_length: np.ndarray = samples.get_z_per_length()
    y_per_length: np.ndarray = samples.get_y_per_length()
    line_length_m: float = samples.get_line_length_m()
    phase_labels: tuple[str, ...] = samples.get_phase_labels()
    sample_count: int = int(frequency_hz.size)
    phase_count: int = int(len(phase_labels))
    sample_index: int

    # Stage 1: validate the global dimensions of the sampled data.
    if sample_count >= 2:
        pass
    else:
        raise ValueError("JMARTI fitting requires at least two frequency samples")

    if line_length_m > 0.0:
        pass
    else:
        raise ValueError("JMARTI fitting requires a strictly positive line length")

    if phase_count >= 1:
        pass
    else:
        raise ValueError("JMARTI fitting requires at least one phase label")

    if z_per_length.shape == (sample_count, phase_count, phase_count):
        pass
    else:
        raise ValueError(
            "JMARTI series impedance samples must have shape "
            f"({sample_count}, {phase_count}, {phase_count}), got {z_per_length.shape}"
        )

    if y_per_length.shape == (sample_count, phase_count, phase_count):
        pass
    else:
        raise ValueError(
            "JMARTI shunt admittance samples must have shape "
            f"({sample_count}, {phase_count}, {phase_count}), got {y_per_length.shape}"
        )

    # Stage 2: require a strictly increasing frequency grid so all derivative and
    # phase-unwrapping steps later on remain well-posed.
    sample_index = 0
    while sample_index < sample_count - 1:
        if frequency_hz[sample_index + 1] > frequency_hz[sample_index]:
            pass
        else:
            raise ValueError("JMARTI frequency samples must be strictly increasing")

        sample_index += 1

    # Stage 3: ensure every sampled matrix stays finite and square. The fitting
    # pipeline can tolerate lossy or weakly coupled data, but not undefined values.
    if np.isfinite(z_per_length).all():
        pass
    else:
        raise ValueError("JMARTI series impedance samples must be finite")

    if np.isfinite(y_per_length).all():
        pass
    else:
        raise ValueError("JMARTI shunt admittance samples must be finite")


def build_jmarti_frequency_samples(frequency_hz: Sequence[float],
                                   z_per_length: np.ndarray,
                                   y_per_length: np.ndarray,
                                   line_length_m: float,
                                   phase_labels: Sequence[str]) -> JMartiFrequencySamples:
    """
    Build one validated JMARTI frequency-sample container.

    :param frequency_hz: Strictly increasing frequency samples in Hz.
    :param z_per_length: Series impedance matrices with shape ``(nf, np, np)``.
    :param y_per_length: Shunt admittance matrices with shape ``(nf, np, np)``.
    :param line_length_m: Physical line length in meters.
    :param phase_labels: Ordered phase labels associated with the matrices.
    :return: Validated frequency-sample container.
    """
    return JMartiFrequencySamples(
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        line_length_m=line_length_m,
        phase_labels=phase_labels,
    )


def build_jmarti_frequency_subset(samples: JMartiFrequencySamples,
                                  low_hz: float,
                                  high_hz: float) -> JMartiFrequencySamples:
    """
    Build one frequency-window subset of a JMARTI sample set.

    :param samples: Full sample set.
    :param low_hz: Lower retained frequency in Hz.
    :param high_hz: Upper retained frequency in Hz.
    :return: Windowed sample set.
    :raises ValueError: If the requested window leaves too few samples.
    """
    frequency_hz: np.ndarray = samples.get_frequency_hz()
    selected_mask: np.ndarray = (frequency_hz >= float(low_hz)) & (frequency_hz <= float(high_hz))

    if int(np.count_nonzero(selected_mask)) >= 2:
        pass
    else:
        raise ValueError("JMARTI frequency subset must keep at least two samples")

    return JMartiFrequencySamples(
        frequency_hz=frequency_hz[selected_mask],
        z_per_length=samples.get_z_per_length()[selected_mask, :, :],
        y_per_length=samples.get_y_per_length()[selected_mask, :, :],
        line_length_m=samples.get_line_length_m(),
        phase_labels=samples.get_phase_labels(),
    )
