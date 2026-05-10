from __future__ import annotations

import numpy as np

from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_fit_options import JMartiFitOptions
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_passivity import evaluate_jmarti_mode_passivity
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_passivity import evaluate_jmarti_passivity_report
from VeraGridEngine.Simulations.EMT.JMARTI_Sim.jmarti_vector_fit import JMartiRationalModeFit


def _build_constant_mode_fit(mode_index: int,
                             target_name: str,
                             constant_term: complex) -> JMartiRationalModeFit:
    """
    Build one constant scalar fit for passivity tests.

    :param mode_index: Modal channel index.
    :param target_name: Scalar target name.
    :param constant_term: Constant response value.
    :return: Constant scalar fit.
    """
    return JMartiRationalModeFit(
        mode_index=mode_index,
        target_name=target_name,
        poles_s=np.zeros(0, dtype=np.complex128),
        residues=np.zeros(0, dtype=np.complex128),
        constant_term=constant_term,
        proportional_term=0.0 + 0.0j,
        fit_error_rms=0.0,
        max_relative_error=0.0,
        iterations_completed=0,
        converged=True,
        stable=True,
    )


def test_jmarti_mode_passivity_accepts_positive_real_yc() -> None:
    fit = _build_constant_mode_fit(mode_index=0, target_name='Yc', constant_term=0.2 + 0.0j)
    options = JMartiFitOptions(passivity_minimum_real_yc_tolerance=1.0e-8)
    report = evaluate_jmarti_mode_passivity(fit, np.asarray([10.0, 100.0, 1000.0], dtype=np.float64), options)

    assert report.get_passes_real_part_check() is True
    assert report.get_minimum_real_part() > 0.0


def test_jmarti_mode_passivity_rejects_negative_real_yc() -> None:
    fit = _build_constant_mode_fit(mode_index=0, target_name='Yc', constant_term=-0.2 + 0.0j)
    options = JMartiFitOptions(passivity_minimum_real_yc_tolerance=1.0e-8)
    report = evaluate_jmarti_mode_passivity(fit, np.asarray([10.0, 100.0, 1000.0], dtype=np.float64), options)

    assert report.get_passes_real_part_check() is False
    assert report.get_minimum_real_part() < 0.0


def test_jmarti_mode_passivity_accepts_bounded_hres() -> None:
    fit = _build_constant_mode_fit(mode_index=1, target_name='Hres', constant_term=0.95 + 0.0j)
    options = JMartiFitOptions(passivity_maximum_hres_gain_tolerance=1.0e-6)
    report = evaluate_jmarti_mode_passivity(fit, np.asarray([10.0, 100.0, 1000.0], dtype=np.float64), options)

    assert report.get_passes_gain_check() is True
    assert report.get_maximum_gain() < 1.0


def test_jmarti_mode_passivity_rejects_amplifying_hres() -> None:
    fit = _build_constant_mode_fit(mode_index=1, target_name='Hres', constant_term=1.05 + 0.0j)
    options = JMartiFitOptions(passivity_maximum_hres_gain_tolerance=1.0e-6)
    report = evaluate_jmarti_mode_passivity(fit, np.asarray([10.0, 100.0, 1000.0], dtype=np.float64), options)

    assert report.get_passes_gain_check() is False
    assert report.get_maximum_gain() > 1.0


def test_jmarti_passivity_report_aggregates_mode_status() -> None:
    fits = [
        _build_constant_mode_fit(mode_index=0, target_name='Yc', constant_term=0.2 + 0.0j),
        _build_constant_mode_fit(mode_index=1, target_name='Hres', constant_term=0.95 + 0.0j),
    ]
    options = JMartiFitOptions(passivity_frequency_sample_count=32)
    report = evaluate_jmarti_passivity_report(fits=fits, low_hz=10.0, high_hz=1000.0, options=options)

    assert report.get_frequency_hz().size == 32
    assert len(report.get_mode_reports()) == 2
    assert report.get_all_checks_pass() is True
