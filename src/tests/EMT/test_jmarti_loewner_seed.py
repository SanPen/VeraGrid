from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import build_jmarti_loewner_left_right_partition
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import build_jmarti_mode_loewner_seed


def _evaluate_scalar_rational_response(frequency_hz: np.ndarray,
                                       poles_s: np.ndarray,
                                       residues: np.ndarray,
                                       direct_term: complex = 0.0 + 0.0j) -> np.ndarray:
    """
    Evaluate one scalar rational response on the imaginary axis.

    :param frequency_hz: Frequency grid in Hz.
    :param poles_s: Continuous-time poles.
    :param residues: Residues paired with ``poles_s``.
    :param direct_term: Optional direct term.
    :return: Complex response samples.
    """
    angular_frequency: np.ndarray = 2.0 * np.pi * frequency_hz
    response: np.ndarray = np.zeros(frequency_hz.size, dtype=np.complex128)
    sample_index: int = 0
    pole_index: int
    s_value: complex

    while sample_index < frequency_hz.size:
        s_value = 1j * angular_frequency[sample_index]
        response[sample_index] = complex(direct_term)
        pole_index = 0

        while pole_index < poles_s.size:
            response[sample_index] = response[sample_index] + residues[pole_index] / (s_value - poles_s[pole_index])
            pole_index += 1

        sample_index += 1

    return response


def test_jmarti_loewner_partition_interleaves_frequency_samples() -> None:
    frequency_hz: np.ndarray = np.asarray([10.0, 20.0, 40.0, 80.0, 160.0, 320.0], dtype=np.float64)
    response: np.ndarray = np.asarray([1.0, 2.0, 3.0, 4.0, 5.0, 6.0], dtype=np.complex128)
    left_frequencies_hz: np.ndarray
    right_frequencies_hz: np.ndarray
    left_response: np.ndarray
    right_response: np.ndarray

    left_frequencies_hz, right_frequencies_hz, left_response, right_response = build_jmarti_loewner_left_right_partition(
        frequency_hz=frequency_hz,
        response_values=response,
        minimum_frequency_samples=4,
    )

    assert np.allclose(left_frequencies_hz, np.asarray([10.0, 40.0, 160.0], dtype=np.float64))
    assert np.allclose(right_frequencies_hz, np.asarray([20.0, 80.0, 320.0], dtype=np.float64))
    assert np.allclose(left_response, np.asarray([1.0, 3.0, 5.0], dtype=np.complex128))
    assert np.allclose(right_response, np.asarray([2.0, 4.0, 6.0], dtype=np.complex128))


def test_jmarti_loewner_seed_recovers_first_order_pole() -> None:
    frequency_hz: np.ndarray = np.logspace(0.0, 3.0, 48, dtype=np.float64)
    exact_poles_s: np.ndarray = np.asarray([-50.0 + 0.0j], dtype=np.complex128)
    residues: np.ndarray = np.asarray([3.0 + 0.0j], dtype=np.complex128)
    response: np.ndarray = _evaluate_scalar_rational_response(frequency_hz, exact_poles_s, residues)
    options = JMartiFitOptions(
        loewner_relative_tolerance=1.0e-10,
        maximum_model_order=3,
    )
    seed = build_jmarti_mode_loewner_seed(
        frequency_hz=frequency_hz,
        response_values=response,
        target_name="Yc",
        mode_index=0,
        options=options,
    )
    recovered_pole_s: complex = seed.get_initial_poles_s()[0]

    assert seed.get_estimated_order() == 1
    assert np.isclose(float(np.real(recovered_pole_s)), -50.0, atol=1.0e-6)
    assert abs(float(np.imag(recovered_pole_s))) < 1.0e-6


def test_jmarti_loewner_seed_recovers_two_real_poles() -> None:
    frequency_hz: np.ndarray = np.logspace(0.0, 4.0, 64, dtype=np.float64)
    exact_poles_s: np.ndarray = np.asarray([-30.0 + 0.0j, -200.0 + 0.0j], dtype=np.complex128)
    residues: np.ndarray = np.asarray([2.0 + 0.0j, 0.5 + 0.0j], dtype=np.complex128)
    response: np.ndarray = _evaluate_scalar_rational_response(frequency_hz, exact_poles_s, residues)
    options = JMartiFitOptions(
        loewner_relative_tolerance=1.0e-10,
        maximum_model_order=4,
    )
    seed = build_jmarti_mode_loewner_seed(
        frequency_hz=frequency_hz,
        response_values=response,
        target_name="Hres",
        mode_index=1,
        options=options,
    )
    recovered_poles_s: np.ndarray = np.sort(np.real(seed.get_initial_poles_s()))

    assert seed.get_estimated_order() == 2
    assert np.isclose(recovered_poles_s[0], -200.0, atol=1.0e-3)
    assert np.isclose(recovered_poles_s[1], -30.0, atol=1.0e-5)
