from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import build_jmarti_mode_loewner_seed
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import build_jmarti_mode_vector_fit
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import evaluate_jmarti_rational_mode_fit


def _evaluate_scalar_rational_response(frequency_hz: np.ndarray,
                                       poles_s: np.ndarray,
                                       residues: np.ndarray,
                                       constant_term: complex = 0.0 + 0.0j,
                                       proportional_term: complex = 0.0 + 0.0j) -> np.ndarray:
    """
    Evaluate one scalar rational response on the imaginary axis.

    :param frequency_hz: Frequency grid in Hz.
    :param poles_s: Continuous-time poles.
    :param residues: Residues paired with ``poles_s``.
    :param constant_term: Optional constant term.
    :param proportional_term: Optional proportional ``s`` term.
    :return: Complex response samples.
    """
    angular_frequency: np.ndarray = 2.0 * np.pi * frequency_hz
    response: np.ndarray = np.zeros(frequency_hz.size, dtype=np.complex128)
    sample_index: int = 0
    pole_index: int
    s_value: complex

    while sample_index < frequency_hz.size:
        s_value = 1j * angular_frequency[sample_index]
        response[sample_index] = complex(constant_term) + complex(proportional_term) * s_value
        pole_index = 0

        while pole_index < poles_s.size:
            response[sample_index] = response[sample_index] + residues[pole_index] / (s_value - poles_s[pole_index])
            pole_index += 1

        sample_index += 1

    return response


def test_jmarti_vector_fit_recovers_first_order_mode() -> None:
    frequency_hz: np.ndarray = np.logspace(0.0, 3.0, 64, dtype=np.float64)
    exact_poles_s: np.ndarray = np.asarray([-50.0 + 0.0j], dtype=np.complex128)
    residues: np.ndarray = np.asarray([3.0 + 0.0j], dtype=np.complex128)
    response: np.ndarray = _evaluate_scalar_rational_response(frequency_hz, exact_poles_s, residues, constant_term=0.2 + 0.0j)
    options = JMartiFitOptions(
        loewner_relative_tolerance=1.0e-10,
        maximum_model_order=3,
        vf_max_iterations=10,
        vf_pole_shift_tolerance=1.0e-8,
        vf_include_constant_term=True,
        vf_include_proportional_term=False,
    )
    loewner_seed = build_jmarti_mode_loewner_seed(
        frequency_hz=frequency_hz,
        response_values=response,
        target_name="Yc",
        mode_index=0,
        options=options,
    )
    fit = build_jmarti_mode_vector_fit(
        frequency_hz=frequency_hz,
        response_values=response,
        loewner_seed=loewner_seed,
        options=options,
    )
    fitted_response: np.ndarray = evaluate_jmarti_rational_mode_fit(fit, frequency_hz)

    assert fit.get_stable() is True
    assert fit.get_fit_error_rms() < 1.0e-8
    assert fit.get_max_relative_error() < 1.0e-7
    assert np.isclose(float(np.real(fit.get_poles_s()[0])), -50.0, atol=1.0e-6)
    assert np.allclose(fitted_response, response, atol=1.0e-8)


def test_jmarti_vector_fit_recovers_two_poles_with_constant_and_proportional_terms() -> None:
    frequency_hz: np.ndarray = np.logspace(0.0, 4.0, 96, dtype=np.float64)
    exact_poles_s: np.ndarray = np.asarray([-30.0 + 0.0j, -200.0 + 0.0j], dtype=np.complex128)
    residues: np.ndarray = np.asarray([2.0 + 0.0j, 0.5 + 0.0j], dtype=np.complex128)
    response: np.ndarray = _evaluate_scalar_rational_response(
        frequency_hz,
        exact_poles_s,
        residues,
        constant_term=0.1 + 0.0j,
        proportional_term=1.0e-4 + 0.0j,
    )
    options = JMartiFitOptions(
        loewner_relative_tolerance=1.0e-10,
        maximum_model_order=4,
        forced_model_order=2,
        vf_max_iterations=12,
        vf_pole_shift_tolerance=1.0e-8,
        vf_include_constant_term=True,
        vf_include_proportional_term=True,
    )
    loewner_seed = build_jmarti_mode_loewner_seed(
        frequency_hz=frequency_hz,
        response_values=response,
        target_name="Hres",
        mode_index=1,
        options=options,
    )
    fit = build_jmarti_mode_vector_fit(
        frequency_hz=frequency_hz,
        response_values=response,
        loewner_seed=loewner_seed,
        options=options,
    )
    fitted_response: np.ndarray = evaluate_jmarti_rational_mode_fit(fit, frequency_hz)
    fitted_poles_s: np.ndarray = np.sort(np.real(fit.get_poles_s()))

    assert fit.get_stable() is True
    assert fit.get_fit_error_rms() < 1.0e-6
    assert fit.get_max_relative_error() < 1.0e-5
    assert np.isclose(fitted_poles_s[0], -200.0, atol=1.0e-2)
    assert np.isclose(fitted_poles_s[1], -30.0, atol=1.0e-4)
    assert np.allclose(fitted_response, response, atol=1.0e-6)
