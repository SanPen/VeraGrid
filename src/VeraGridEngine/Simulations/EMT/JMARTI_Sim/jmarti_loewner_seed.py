# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np
import scipy.linalg as la

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions


class JMartiModeLoewnerSeed:
    """
    Loewner-based order and pole seed for one scalar JMARTI modal target.

    The class stores the reduced-order information that later feeds the Vector
    Fitting stage. The seed is intentionally scalar per mode because the first
    JMARTI implementation in VeraGrid fits each modal channel independently.
    """

    __slots__ = (
        '_mode_index',
        '_target_name',
        '_left_frequencies_hz',
        '_right_frequencies_hz',
        '_singular_values',
        '_estimated_order',
        '_initial_poles_s',
        '_truncation_ratio',
    )

    def __init__(self,
                 mode_index: int,
                 target_name: str,
                 left_frequencies_hz: np.ndarray,
                 right_frequencies_hz: np.ndarray,
                 singular_values: np.ndarray,
                 estimated_order: int,
                 initial_poles_s: np.ndarray,
                 truncation_ratio: float) -> None:
        """
        Store one Loewner seed bundle for a scalar modal target.

        :param mode_index: Modal channel index.
        :param target_name: Modal target name, for example ``Yc`` or ``Hres``.
        :param left_frequencies_hz: Left sample subset in Hz.
        :param right_frequencies_hz: Right sample subset in Hz.
        :param singular_values: Singular values of the Loewner matrix.
        :param estimated_order: Estimated reduced rational order.
        :param initial_poles_s: Initial poles in the continuous-time s-plane.
        :param truncation_ratio: First discarded-to-leading singular-value ratio.
        :return: None.
        """
        self._mode_index: int = int(mode_index)
        self._target_name: str = str(target_name)
        self._left_frequencies_hz: np.ndarray = np.asarray(left_frequencies_hz, dtype=np.float64)
        self._right_frequencies_hz: np.ndarray = np.asarray(right_frequencies_hz, dtype=np.float64)
        self._singular_values: np.ndarray = np.asarray(singular_values, dtype=np.float64)
        self._estimated_order: int = int(estimated_order)
        self._initial_poles_s: np.ndarray = np.asarray(initial_poles_s, dtype=np.complex128)
        self._truncation_ratio: float = float(truncation_ratio)

    def get_mode_index(self) -> int:
        """
        Return the modal channel index.

        :return: Modal channel index.
        """
        return self._mode_index

    def get_target_name(self) -> str:
        """
        Return the scalar target name.

        :return: Target name.
        """
        return self._target_name

    def get_left_frequencies_hz(self) -> np.ndarray:
        """
        Return the left frequency subset.

        :return: Left sample frequencies in Hz.
        """
        return self._left_frequencies_hz

    def get_right_frequencies_hz(self) -> np.ndarray:
        """
        Return the right frequency subset.

        :return: Right sample frequencies in Hz.
        """
        return self._right_frequencies_hz

    def get_singular_values(self) -> np.ndarray:
        """
        Return the singular values of the Loewner matrix.

        :return: Singular-value vector.
        """
        return self._singular_values

    def get_estimated_order(self) -> int:
        """
        Return the estimated reduced order.

        :return: Reduced order.
        """
        return self._estimated_order

    def get_initial_poles_s(self) -> np.ndarray:
        """
        Return the initial continuous-time poles.

        :return: Complex pole vector.
        """
        return self._initial_poles_s

    def get_truncation_ratio(self) -> float:
        """
        Return the first discarded-to-leading singular-value ratio.

        :return: Truncation ratio.
        """
        return self._truncation_ratio


def build_jmarti_loewner_left_right_partition(frequency_hz: np.ndarray,
                                              response_values: np.ndarray,
                                              minimum_frequency_samples: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split one scalar frequency response into interleaved left and right subsets.

    The Loewner framework requires two disjoint sampling sets. Interleaving the
    original frequency grid preserves broad-band coverage on both sides without
    introducing user-tuned partition heuristics in the first implementation.

    :param frequency_hz: Strictly increasing frequency samples in Hz.
    :param response_values: Complex scalar response samples on the same grid.
    :param minimum_frequency_samples: Minimum number of total samples required by the user options.
    :return: Tuple ``(left_f_hz, right_f_hz, left_resp, right_resp)``.
    :raises ValueError: If the sample vectors are too short or inconsistent.
    """
    sample_count: int = int(frequency_hz.size)

    # Stage 1: validate that a non-trivial left/right partition is possible.
    if response_values.shape == (sample_count,):
        pass
    else:
        raise ValueError("Loewner seed expects a one-dimensional scalar response vector")

    if sample_count >= int(minimum_frequency_samples):
        pass
    else:
        raise ValueError(
            "Loewner seed requires at least "
            f"{int(minimum_frequency_samples)} scalar frequency samples"
        )

    # Stage 2: interleave samples so both subsets span the whole frequency band.
    left_frequencies_hz: np.ndarray = np.asarray(frequency_hz[0::2], dtype=np.float64)
    right_frequencies_hz: np.ndarray = np.asarray(frequency_hz[1::2], dtype=np.float64)
    left_response: np.ndarray = np.asarray(response_values[0::2], dtype=np.complex128)
    right_response: np.ndarray = np.asarray(response_values[1::2], dtype=np.complex128)

    if left_frequencies_hz.size >= 2 and right_frequencies_hz.size >= 2:
        pass
    else:
        raise ValueError("Loewner seed requires at least two samples in both left and right subsets")

    return left_frequencies_hz, right_frequencies_hz, left_response, right_response


def build_jmarti_loewner_matrices(left_frequencies_hz: np.ndarray,
                                  right_frequencies_hz: np.ndarray,
                                  left_response: np.ndarray,
                                  right_response: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build the Loewner and shifted-Loewner matrices for one scalar response.

    :param left_frequencies_hz: Left frequency subset in Hz.
    :param right_frequencies_hz: Right frequency subset in Hz.
    :param left_response: Complex response samples on the left subset.
    :param right_response: Complex response samples on the right subset.
    :return: Tuple ``(L, Ls)``.
    """
    # Stage 1: lift the frequency samples onto the continuous-time imaginary axis.
    left_s_plane: np.ndarray = 1j * 2.0 * np.pi * left_frequencies_hz
    right_s_plane: np.ndarray = 1j * 2.0 * np.pi * right_frequencies_hz
    denominator: np.ndarray = left_s_plane[:, None] - right_s_plane[None, :]

    # Stage 2: build the classical scalar Loewner pair through broadcasting.
    loewner_matrix: np.ndarray = (left_response[:, None] - right_response[None, :]) / denominator
    shifted_loewner_matrix: np.ndarray = (
        left_s_plane[:, None] * left_response[:, None]
        - right_s_plane[None, :] * right_response[None, :]
    ) / denominator
    return loewner_matrix, shifted_loewner_matrix


def estimate_jmarti_loewner_order(singular_values: np.ndarray,
                                  relative_tolerance: float,
                                  maximum_order: int,
                                  forced_model_order: int) -> Tuple[int, float]:
    """
    Estimate one reduced order from Loewner singular values.

    :param singular_values: Singular-value vector in descending order.
    :param relative_tolerance: Relative truncation tolerance.
    :param maximum_order: Optional maximum order clamp.
    :param forced_model_order: Fixed user order. ``0`` means automatic.
    :return: Tuple ``(estimated_order, truncation_ratio)``.
    """
    singular_count: int = int(singular_values.size)
    leading_value: float
    order_index: int = 0
    estimated_order: int = 0
    truncation_ratio: float

    if singular_count >= 1:
        pass
    else:
        raise ValueError("Loewner order estimation requires at least one singular value")

    if forced_model_order > 0:
        estimated_order = min(int(forced_model_order), int(maximum_order), singular_count)
    else:
        leading_value = float(singular_values[0])

        if leading_value > 0.0:
            pass
        else:
            leading_value = 1.0

        while order_index < singular_count:
            if singular_values[order_index] > relative_tolerance * leading_value:
                estimated_order += 1
            else:
                pass
            order_index += 1

        estimated_order = min(estimated_order, int(maximum_order))

        if estimated_order >= 1:
            pass
        else:
            estimated_order = 1

    if estimated_order < singular_count:
        if singular_values[0] > 0.0:
            truncation_ratio = float(singular_values[estimated_order] / singular_values[0])
        else:
            truncation_ratio = 0.0
    else:
        truncation_ratio = 0.0

    return estimated_order, truncation_ratio


def extract_jmarti_loewner_initial_poles(loewner_matrix: np.ndarray,
                                         shifted_loewner_matrix: np.ndarray,
                                         estimated_order: int) -> np.ndarray:
    """
    Extract one set of continuous-time poles from the reduced Loewner pencil.

    :param loewner_matrix: Loewner matrix.
    :param shifted_loewner_matrix: Shifted Loewner matrix.
    :param estimated_order: Reduced order used for projection.
    :return: Complex initial pole vector.
    """
    u_matrix: np.ndarray
    singular_values: np.ndarray
    vh_matrix: np.ndarray
    reduced_u: np.ndarray
    reduced_v: np.ndarray
    reduced_loewner: np.ndarray
    reduced_shifted_loewner: np.ndarray
    poles_s: np.ndarray

    # Stage 1: build the projection basis from the Loewner matrix itself.
    u_matrix, singular_values, vh_matrix = la.svd(loewner_matrix, full_matrices=False)
    reduced_u = u_matrix[:, :estimated_order]
    reduced_v = vh_matrix.conj().T[:, :estimated_order]
    reduced_loewner = reduced_u.conj().T @ loewner_matrix @ reduced_v
    reduced_shifted_loewner = reduced_u.conj().T @ shifted_loewner_matrix @ reduced_v

    # Stage 2: solve the reduced generalized eigenproblem. The signs cancel on
    # both matrices, so the standard pair directly yields the continuous-time poles.
    poles_s = la.eigvals(reduced_shifted_loewner, reduced_loewner)
    return np.asarray(poles_s, dtype=np.complex128)


def build_jmarti_mode_loewner_seed(frequency_hz: Sequence[float],
                                   response_values: np.ndarray,
                                   target_name: str,
                                   mode_index: int,
                                   options: JMartiFitOptions | None = None) -> JMartiModeLoewnerSeed:
    """
    Build one Loewner seed bundle for a scalar JMARTI modal target.

    :param frequency_hz: Strictly increasing frequency grid in Hz.
    :param response_values: Complex scalar response samples on that grid.
    :param target_name: Modal target name, for example ``Yc`` or ``Hres``.
    :param mode_index: Modal channel index.
    :param options: Optional user-configurable JMARTI fitting options.
    :return: Loewner seed bundle.
    """
    resolved_options: JMartiFitOptions = JMartiFitOptions() if options is None else options
    frequency_array: np.ndarray = np.asarray(frequency_hz, dtype=np.float64)
    response_array: np.ndarray = np.asarray(response_values, dtype=np.complex128)
    left_frequencies_hz: np.ndarray
    right_frequencies_hz: np.ndarray
    left_response: np.ndarray
    right_response: np.ndarray
    loewner_matrix: np.ndarray
    shifted_loewner_matrix: np.ndarray
    singular_values: np.ndarray
    estimated_order: int
    truncation_ratio: float
    initial_poles_s: np.ndarray

    left_frequencies_hz, right_frequencies_hz, left_response, right_response = build_jmarti_loewner_left_right_partition(
        frequency_hz=frequency_array,
        response_values=response_array,
        minimum_frequency_samples=resolved_options.get_minimum_frequency_samples(),
    )
    loewner_matrix, shifted_loewner_matrix = build_jmarti_loewner_matrices(
        left_frequencies_hz=left_frequencies_hz,
        right_frequencies_hz=right_frequencies_hz,
        left_response=left_response,
        right_response=right_response,
    )

    # Stage 1: use the Loewner singular spectrum to estimate a reduced order.
    singular_values = np.asarray(la.svd(loewner_matrix, compute_uv=False), dtype=np.float64)
    estimated_order, truncation_ratio = estimate_jmarti_loewner_order(
        singular_values=singular_values,
        relative_tolerance=resolved_options.get_loewner_relative_tolerance(),
        maximum_order=resolved_options.get_maximum_model_order(),
        forced_model_order=resolved_options.get_forced_model_order(),
    )

    # Stage 2: extract a first set of poles for the later VF refinement.
    initial_poles_s = extract_jmarti_loewner_initial_poles(
        loewner_matrix=loewner_matrix,
        shifted_loewner_matrix=shifted_loewner_matrix,
        estimated_order=estimated_order,
    )

    return JMartiModeLoewnerSeed(
        mode_index=mode_index,
        target_name=target_name,
        left_frequencies_hz=left_frequencies_hz,
        right_frequencies_hz=right_frequencies_hz,
        singular_values=singular_values,
        estimated_order=estimated_order,
        initial_poles_s=initial_poles_s,
        truncation_ratio=truncation_ratio,
    )
