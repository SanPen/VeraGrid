from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_bundle import build_jmarti_fit_bundle
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import build_jmarti_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_loewner_seed import build_jmarti_mode_loewner_seed
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import build_jmarti_modal_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import estimate_jmarti_mode_delays
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_passivity import evaluate_jmarti_passivity_report
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_runtime_data import build_jmarti_runtime_data
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import build_jmarti_mode_vector_fit


def _evaluate_scalar_rational_response(frequency_hz: np.ndarray,
                                       poles_s: np.ndarray,
                                       residues: np.ndarray,
                                       constant_term: complex = 0.0 + 0.0j) -> np.ndarray:
    """
    Evaluate one scalar rational response on the imaginary axis.

    :param frequency_hz: Frequency grid in Hz.
    :param poles_s: Continuous-time poles.
    :param residues: Residues paired with ``poles_s``.
    :param constant_term: Optional constant term.
    :return: Complex response samples.
    """
    angular_frequency: np.ndarray = 2.0 * np.pi * frequency_hz
    response: np.ndarray = np.zeros(frequency_hz.size, dtype=np.complex128)
    sample_index: int = 0
    pole_index: int
    s_value: complex

    while sample_index < frequency_hz.size:
        s_value = 1j * angular_frequency[sample_index]
        response[sample_index] = complex(constant_term)
        pole_index = 0

        while pole_index < poles_s.size:
            response[sample_index] = response[sample_index] + residues[pole_index] / (s_value - poles_s[pole_index])
            pole_index += 1

        sample_index += 1

    return response


def _build_diagonal_modal_bundle() -> tuple[object, object]:
    """
    Build one small self-consistent JMARTI fit bundle and runtime dataset.

    :return: Tuple ``(fit_bundle, runtime_data)``.
    """
    frequency_hz: np.ndarray = np.asarray([10.0, 40.0, 80.0, 160.0, 320.0, 640.0], dtype=np.float64)
    z_per_length: np.ndarray = np.zeros((frequency_hz.size, 2, 2), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((frequency_hz.size, 2, 2), dtype=np.complex128)
    mode0_pole_s: np.ndarray = np.asarray([-50.0 + 0.0j], dtype=np.complex128)
    mode1_pole_s: np.ndarray = np.asarray([-120.0 + 0.0j], dtype=np.complex128)
    mode0_residue: np.ndarray = np.asarray([0.3 + 0.0j], dtype=np.complex128)
    mode1_residue: np.ndarray = np.asarray([0.15 + 0.0j], dtype=np.complex128)
    hres_mode0_pole_s: np.ndarray = np.asarray([-80.0 + 0.0j], dtype=np.complex128)
    hres_mode1_pole_s: np.ndarray = np.asarray([-160.0 + 0.0j], dtype=np.complex128)
    hres_mode0_residue: np.ndarray = np.asarray([0.02 + 0.0j], dtype=np.complex128)
    hres_mode1_residue: np.ndarray = np.asarray([0.01 + 0.0j], dtype=np.complex128)
    sample_index: int = 0
    mode_response_yc: np.ndarray
    mode0_response_hres: np.ndarray
    mode1_response_hres: np.ndarray
    options: JMartiFitOptions
    samples = None
    modal_samples = None
    mode_delays = None
    yc_fit_mode0 = None
    yc_fit_mode1 = None
    hres_fit_mode0 = None
    hres_fit_mode1 = None
    passivity_report = None
    fit_bundle = None
    runtime_data = None

    mode_response_yc = _evaluate_scalar_rational_response(frequency_hz, mode0_pole_s, mode0_residue, constant_term=0.1 + 0.0j)
    mode0_response_hres = _evaluate_scalar_rational_response(frequency_hz, hres_mode0_pole_s, hres_mode0_residue, constant_term=0.85 + 0.0j)
    mode1_response_hres = _evaluate_scalar_rational_response(frequency_hz, hres_mode1_pole_s, hres_mode1_residue, constant_term=0.75 + 0.0j)

    while sample_index < frequency_hz.size:
        z_per_length[sample_index, :, :] = np.diag(np.asarray([
            1.0 + 0.2j * float(sample_index + 1),
            2.0 + 0.3j * float(sample_index + 1),
        ], dtype=np.complex128))
        y_per_length[sample_index, :, :] = np.diag(np.asarray([
            mode_response_yc[sample_index] * mode_response_yc[sample_index],
            mode1_response_hres[sample_index] * mode1_response_hres[sample_index],
        ], dtype=np.complex128))
        sample_index += 1

    options = JMartiFitOptions(
        forced_model_order=1,
        vf_max_iterations=8,
        passivity_frequency_sample_count=64,
    )
    samples = build_jmarti_frequency_samples(
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        line_length_m=1000.0,
        phase_labels=("A", "B"),
    )
    modal_samples = build_jmarti_modal_samples(samples=samples, options=options)
    mode_delays = estimate_jmarti_mode_delays(modal_samples, options=options)
    yc_fit_mode0 = build_jmarti_mode_vector_fit(
        frequency_hz=frequency_hz,
        response_values=modal_samples.get_yc_modal()[:, 0],
        loewner_seed=build_jmarti_mode_loewner_seed(frequency_hz, modal_samples.get_yc_modal()[:, 0], "Yc", 0, options),
        options=options,
    )
    yc_fit_mode1 = build_jmarti_mode_vector_fit(
        frequency_hz=frequency_hz,
        response_values=modal_samples.get_yc_modal()[:, 1],
        loewner_seed=build_jmarti_mode_loewner_seed(frequency_hz, modal_samples.get_yc_modal()[:, 1], "Yc", 1, options),
        options=options,
    )
    hres_fit_mode0 = build_jmarti_mode_vector_fit(
        frequency_hz=frequency_hz,
        response_values=mode0_response_hres,
        loewner_seed=build_jmarti_mode_loewner_seed(frequency_hz, mode0_response_hres, "Hres", 0, options),
        options=options,
    )
    hres_fit_mode1 = build_jmarti_mode_vector_fit(
        frequency_hz=frequency_hz,
        response_values=mode1_response_hres,
        loewner_seed=build_jmarti_mode_loewner_seed(frequency_hz, mode1_response_hres, "Hres", 1, options),
        options=options,
    )
    passivity_report = evaluate_jmarti_passivity_report(
        fits=[yc_fit_mode0, yc_fit_mode1, hres_fit_mode0, hres_fit_mode1],
        low_hz=10.0,
        high_hz=640.0,
        options=options,
    )
    fit_bundle = build_jmarti_fit_bundle(
        modal_samples=modal_samples,
        mode_delays=mode_delays,
        yc_fits=[yc_fit_mode0, yc_fit_mode1],
        hres_fits=[hres_fit_mode0, hres_fit_mode1],
        passivity_report=passivity_report,
    )
    runtime_data = build_jmarti_runtime_data(fit_bundle=fit_bundle, time_step_s=1.0e-4)
    return fit_bundle, runtime_data


def test_jmarti_fit_bundle_keeps_mode_alignment_and_optional_passivity_report() -> None:
    fit_bundle, _runtime_data = _build_diagonal_modal_bundle()

    assert fit_bundle.get_mode_count() == 2
    assert fit_bundle.get_passivity_report() is not None
    assert fit_bundle.get_yc_fits()[0].get_mode_index() == 0
    assert fit_bundle.get_hres_fits()[1].get_mode_index() == 1


def test_jmarti_runtime_data_builds_exact_discrete_coefficients_and_delay_split() -> None:
    fit_bundle, runtime_data = _build_diagonal_modal_bundle()
    mode_data = runtime_data.get_mode_data()[0]
    expected_alpha = np.exp(fit_bundle.get_yc_fits()[0].get_poles_s() * runtime_data.get_time_step_s())

    assert runtime_data.get_mode_count() == 2
    assert mode_data.get_delay_step_count() >= 0
    assert mode_data.get_residual_delay_s() >= 0.0
    assert np.allclose(mode_data.get_yc_alpha(), expected_alpha, atol=1.0e-12)
