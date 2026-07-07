# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

from pathlib import Path

import numpy as np

import VeraGridEngine.api as gce
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_fit_bundle_from_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import build_jmarti_frequency_samples_from_line
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_frequency_samples import build_jmarti_frequency_samples
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_workflow import load_jmarti_frequency_samples_from_npz


def test_jmarti_fit_workflow_builds_one_bundle_from_frequency_samples() -> None:
    frequency_hz: np.ndarray = np.asarray([10.0, 40.0, 80.0, 160.0, 320.0, 640.0], dtype=np.float64)
    angular_frequency: np.ndarray = 2.0 * np.pi * frequency_hz
    z_per_length: np.ndarray = np.zeros((frequency_hz.size, 3, 3), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((frequency_hz.size, 3, 3), dtype=np.complex128)
    resistance_values: np.ndarray = np.asarray([0.20, 0.24, 0.28], dtype=np.float64)
    inductance_values: np.ndarray = np.asarray([1.0e-3, 1.2e-3, 1.4e-3], dtype=np.float64)
    capacitance_values: np.ndarray = np.asarray([9.0e-9, 8.0e-9, 7.0e-9], dtype=np.float64)
    sample_index: int = 0
    options: JMartiFitOptions = JMartiFitOptions(forced_model_order=1, vf_max_iterations=6)

    while sample_index < frequency_hz.size:
        z_per_length[sample_index, :, :] = np.diag(
            resistance_values + 1j * angular_frequency[sample_index] * inductance_values
        )
        y_per_length[sample_index, :, :] = np.diag(
            1j * angular_frequency[sample_index] * capacitance_values
        )
        sample_index += 1

    fit_bundle = build_jmarti_fit_bundle_from_frequency_samples(
        samples=build_jmarti_frequency_samples(
            frequency_hz=frequency_hz,
            z_per_length=z_per_length,
            y_per_length=y_per_length,
            line_length_m=1000.0,
            phase_labels=("A", "B", "C"),
        ),
        options=options,
    )

    assert fit_bundle.get_mode_count() == 3
    assert fit_bundle.get_frequency_hz().shape == frequency_hz.shape
    assert fit_bundle.get_passivity_report() is not None
    assert fit_bundle.get_passivity_report().get_all_checks_pass()
    assert len(fit_bundle.get_yc_fits()) == 3
    assert len(fit_bundle.get_hres_fits()) == 3


def test_jmarti_frequency_samples_from_line_uses_nominal_overhead_data_and_selected_phases() -> None:
    bus0 = gce.Bus(name="Bus0", Vnom=13.8)
    bus1 = gce.Bus(name="Bus1", Vnom=13.8)
    line_template = gce.create_known_abc_overhead_template(
        name="KnownOverhead",
        z_nabc=np.asarray([
            [0.12 + 1j * 0.31, 0.01 + 1j * 0.02, 0.00 + 1j * 0.01],
            [0.01 + 1j * 0.02, 0.13 + 1j * 0.33, 0.02 + 1j * 0.02],
            [0.00 + 1j * 0.01, 0.02 + 1j * 0.02, 0.14 + 1j * 0.35],
        ], dtype=np.complex128),
        ysh_nabc=np.asarray([
            [0.0 + 1j * 3.0e-6, 0.0 - 1j * 2.0e-7, 0.0 - 1j * 1.0e-7],
            [0.0 - 1j * 2.0e-7, 0.0 + 1j * 3.2e-6, 0.0 - 1j * 2.0e-7],
            [0.0 - 1j * 1.0e-7, 0.0 - 1j * 2.0e-7, 0.0 + 1j * 3.4e-6],
        ], dtype=np.complex128),
        phases=np.asarray([1, 2, 3], dtype=np.int64),
        frequency=60.0,
    )
    line = gce.Line(name="LineForGuiFit", bus_from=bus0, bus_to=bus1, length=2.5, template=line_template)

    samples = build_jmarti_frequency_samples_from_line(
        line=line,
        phase_n=False,
        phase_a=True,
        phase_b=False,
        phase_c=True,
        low_hz=10.0,
        high_hz=640.0,
        sample_count=6,
        sbase_mva=25.0,
    )

    assert samples.get_phase_labels() == ("A", "C")
    assert samples.get_line_length_m() == 2500.0
    assert samples.get_z_per_length().shape == (6, 2, 2)
    assert samples.get_y_per_length().shape == (6, 2, 2)
    assert float(np.imag(samples.get_z_per_length()[0, 0, 0])) < float(np.imag(samples.get_z_per_length()[-1, 0, 0]))
    assert float(np.imag(samples.get_y_per_length()[0, 0, 0])) < float(np.imag(samples.get_y_per_length()[-1, 0, 0]))


def test_jmarti_frequency_samples_from_line_supports_sequence_line_templates() -> None:
    bus0 = gce.Bus(name="BusSeq0", Vnom=110.0)
    bus1 = gce.Bus(name="BusSeq1", Vnom=110.0)
    line = gce.Line(
        name="SequenceLineForGuiFit",
        bus_from=bus0,
        bus_to=bus1,
        length=5.0,
        template=gce.SequenceLineType(
            R=0.12,
            X=0.35,
            B=3.0,
            R0=0.28,
            X0=0.78,
            B0=1.8,
        ),
    )

    samples = build_jmarti_frequency_samples_from_line(
        line=line,
        phase_n=False,
        phase_a=True,
        phase_b=True,
        phase_c=True,
        low_hz=10.0,
        high_hz=640.0,
        sample_count=6,
        nominal_frequency_hz=50.0,
        sbase_mva=100.0,
    )

    assert samples.get_phase_labels() == ("A", "B", "C")
    assert samples.get_z_per_length().shape == (6, 3, 3)
    assert samples.get_y_per_length().shape == (6, 3, 3)
    assert float(np.imag(samples.get_z_per_length()[0, 0, 0])) < float(np.imag(samples.get_z_per_length()[-1, 0, 0]))
    assert float(np.imag(samples.get_y_per_length()[0, 0, 0])) < float(np.imag(samples.get_y_per_length()[-1, 0, 0]))


def test_jmarti_frequency_samples_from_line_supports_underground_line_templates() -> None:
    bus0 = gce.Bus(name="BusCable0", Vnom=33.0)
    bus1 = gce.Bus(name="BusCable1", Vnom=33.0)
    line = gce.Line(
        name="CableLineForGuiFit",
        bus_from=bus0,
        bus_to=bus1,
        length=3.0,
        template=gce.UndergroundLineType(
            R=0.09,
            X=0.22,
            C=0.25,
            R0=0.17,
            X0=0.52,
            C0=0.12,
            freq=60.0,
        ),
    )

    samples = build_jmarti_frequency_samples_from_line(
        line=line,
        phase_n=False,
        phase_a=True,
        phase_b=False,
        phase_c=True,
        low_hz=10.0,
        high_hz=640.0,
        sample_count=6,
        sbase_mva=100.0,
    )

    assert samples.get_phase_labels() == ("A", "C")
    assert samples.get_z_per_length().shape == (6, 2, 2)
    assert samples.get_y_per_length().shape == (6, 2, 2)
    assert float(np.imag(samples.get_z_per_length()[0, 0, 0])) < float(np.imag(samples.get_z_per_length()[-1, 0, 0]))
    assert float(np.imag(samples.get_y_per_length()[0, 0, 0])) < float(np.imag(samples.get_y_per_length()[-1, 0, 0]))


def test_jmarti_frequency_samples_can_be_imported_from_npz(tmp_path: Path) -> None:
    frequency_hz: np.ndarray = np.asarray([5.0, 25.0, 125.0], dtype=np.float64)
    z_per_length: np.ndarray = np.zeros((3, 4, 4), dtype=np.complex128)
    y_per_length: np.ndarray = np.zeros((3, 4, 4), dtype=np.complex128)
    sample_index: int = 0
    npz_path: Path = tmp_path / "jmarti_import_samples.npz"

    while sample_index < 3:
        z_per_length[sample_index, :, :] = np.diag(
            np.asarray([
                0.01 + 1j * (0.05 + 0.01 * sample_index),
                0.02 + 1j * (0.06 + 0.01 * sample_index),
                0.03 + 1j * (0.07 + 0.01 * sample_index),
                0.04 + 1j * (0.08 + 0.01 * sample_index),
            ], dtype=np.complex128)
        )
        y_per_length[sample_index, :, :] = np.diag(
            np.asarray([
                1j * (1.0e-6 + 1.0e-7 * sample_index),
                1j * (1.1e-6 + 1.0e-7 * sample_index),
                1j * (1.2e-6 + 1.0e-7 * sample_index),
                1j * (1.3e-6 + 1.0e-7 * sample_index),
            ], dtype=np.complex128)
        )
        sample_index += 1

    np.savez(
        npz_path,
        frequency_hz=frequency_hz,
        z_per_length=z_per_length,
        y_per_length=y_per_length,
        phase_labels=np.asarray(["N", "A", "B", "C"]),
    )

    samples = load_jmarti_frequency_samples_from_npz(
        file_path=str(npz_path),
        phase_n=False,
        phase_a=True,
        phase_b=False,
        phase_c=True,
        fallback_line_length_m=1800.0,
    )

    assert samples.get_phase_labels() == ("A", "C")
    assert samples.get_line_length_m() == 1800.0
    assert samples.get_z_per_length().shape == (3, 2, 2)
    assert samples.get_y_per_length().shape == (3, 2, 2)
