from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import build_jmarti_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import build_jmarti_modal_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import estimate_jmarti_mode_delays


def test_jmarti_frequency_samples_validate_shapes_and_strict_frequency_order() -> None:
    frequency_hz: np.ndarray = np.asarray([10.0, 100.0, 1000.0], dtype=np.float64)
    z_per_length: np.ndarray = np.zeros((3, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((3, 3, 3), dtype=np.complex128)
    sample_index: int = 0

    while sample_index < 3:
        z_per_length[sample_index, :, :] = np.eye(3, dtype=np.complex128) * (1.0 + 1j * float(sample_index + 1))
        y_per_length[sample_index, :, :] = np.eye(3, dtype=np.complex128) * (0.1 + 1j * float(sample_index + 1))
        sample_index += 1

    samples = build_jmarti_frequency_samples(
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        line_length_m=1000.0,
        phase_labels=("A", "B", "C"),
    )

    assert samples.get_frequency_count() == 3
    assert samples.get_phase_count() == 3


def test_jmarti_modal_samples_recover_one_constant_diagonal_modal_basis() -> None:
    frequency_hz: np.ndarray = np.asarray([10.0, 100.0, 500.0, 1000.0], dtype=np.float64)
    transform: np.ndarray = np.asarray([
        [1.0, 1.0, 0.0],
        [1.0, -1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], dtype=np.complex128)
    transform_inv: np.ndarray = np.linalg.inv(transform)
    z_per_length: np.ndarray = np.zeros((4, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((4, 3, 3), dtype=np.complex128)
    sample_index: int = 0

    while sample_index < 4:
        z_modal_diag: np.ndarray = np.asarray([
            1.0 + 1j * float(sample_index + 1),
            2.0 + 1j * 2.0 * float(sample_index + 1),
            3.0 + 1j * 3.0 * float(sample_index + 1),
        ], dtype=np.complex128)
        y_modal_diag: np.ndarray = np.asarray([
            0.2 + 1j * 0.5 * float(sample_index + 1),
            0.3 + 1j * 0.7 * float(sample_index + 1),
            0.4 + 1j * 0.9 * float(sample_index + 1),
        ], dtype=np.complex128)
        z_modal_matrix: np.ndarray = np.diag(z_modal_diag)
        y_modal_matrix: np.ndarray = np.diag(y_modal_diag)
        z_per_length[sample_index, :, :] = transform @ z_modal_matrix @ transform_inv
        y_per_length[sample_index, :, :] = transform @ y_modal_matrix @ transform_inv
        sample_index += 1

    samples = build_jmarti_frequency_samples(
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        line_length_m=1000.0,
        phase_labels=("A", "B", "C"),
    )
    options = JMartiFitOptions(reference_frequency_hz=100.0)
    modal_samples = build_jmarti_modal_samples(samples=samples, options=options)

    assert float(np.max(modal_samples.get_decoupling_error_z())) < 1.0e-12
    assert float(np.max(modal_samples.get_decoupling_error_y())) < 1.0e-12


def test_jmarti_mode_delay_estimator_recovers_affine_phase_delay() -> None:
    frequency_hz: np.ndarray = np.asarray([10.0, 40.0, 80.0, 160.0, 320.0], dtype=np.float64)
    omega: np.ndarray = 2.0 * np.pi * frequency_hz
    line_length_m: float = 1000.0
    tau_values: np.ndarray = np.asarray([2.0e-4, 4.0e-4, 7.0e-4], dtype=np.float64)
    alpha_values: np.ndarray = np.asarray([1.0e-5, 2.0e-5, 3.0e-5], dtype=np.float64)
    gamma_modal: np.ndarray = np.zeros((frequency_hz.size, 3), dtype=np.complex128)
    z_modal_diag: np.ndarray = np.ones((frequency_hz.size, 3), dtype=np.complex128)
    y_modal_diag: np.ndarray = np.ones((frequency_hz.size, 3), dtype=np.complex128)
    z_modal: np.ndarray = np.zeros((frequency_hz.size, 3, 3), dtype=np.complex128)
    y_modal: np.ndarray = np.zeros((frequency_hz.size, 3, 3), dtype=np.complex128)
    sample_index: int = 0
    mode_index: int

    while sample_index < frequency_hz.size:
        mode_index = 0
        while mode_index < 3:
            gamma_modal[sample_index, mode_index] = (
                alpha_values[mode_index]
                + 1j * tau_values[mode_index] * omega[sample_index] / line_length_m
            )
            mode_index += 1

        z_modal[sample_index, :, :] = np.eye(3, dtype=np.complex128)
        y_modal[sample_index, :, :] = np.eye(3, dtype=np.complex128)
        sample_index += 1

    from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_modal_processing import JMartiModalSamples

    modal_samples = JMartiModalSamples(
        frequency_hz=frequency_hz,
        line_length_m=line_length_m,
        phase_labels=("A", "B", "C"),
        modal_transform=np.eye(3, dtype=np.complex128),
        modal_transform_inv=np.eye(3, dtype=np.complex128),
        z_modal=z_modal,
        y_modal=y_modal,
        z_modal_diag=z_modal_diag,
        y_modal_diag=y_modal_diag,
        gamma_modal=gamma_modal,
        yc_modal=np.ones((frequency_hz.size, 3), dtype=np.complex128),
        decoupling_error_z=np.zeros(frequency_hz.size, dtype=np.float64),
        decoupling_error_y=np.zeros(frequency_hz.size, dtype=np.float64),
        reference_frequency_hz=80.0,
    )
    options = JMartiFitOptions(use_delay_fit_window=True, delay_fit_low_hz=40.0, delay_fit_high_hz=320.0)
    delay_estimates = estimate_jmarti_mode_delays(modal_samples, options=options)

    assert len(delay_estimates) == 3
    assert np.isclose(delay_estimates[0].get_tau_s(), tau_values[0], atol=1.0e-10)
    assert np.isclose(delay_estimates[1].get_tau_s(), tau_values[1], atol=1.0e-10)
    assert np.isclose(delay_estimates[2].get_tau_s(), tau_values[2], atol=1.0e-10)
