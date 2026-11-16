# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Steady-state source equations for PSS/E CIMTR induction models."""

import math

import numpy as np
import pytest

from VeraGridEngine.Templates.Rms.induction_machines.cimtr_operating_point import (
    CimtrOperatingPoint,
    _cimtr_equilibrium_residual,
    solve_cimtr_operating_point,
)
from VeraGridEngine.enumerations import InductionMachineRole


@pytest.mark.parametrize(
    ('role', 'active_power', 'reactive_power'),
    (
        (InductionMachineRole.GENERATOR, 1.0, 0.2),
        (InductionMachineRole.MOTOR, 1.0, 0.2),
    ),
)
def test_cimtr_operating_point_satisfies_source_equilibrium(
        role: InductionMachineRole,
        active_power: float,
        reactive_power: float,
) -> None:
    """Solve and check flux, stator, power, slip, and shunt equations."""
    voltage_magnitude: float = 0.8
    voltage_angle: float = 0.4
    nominal_frequency_hz: float = 60.0
    resistance: float = 0.015
    x: float = 3.0
    x_prime: float = 0.3
    x_double_prime: float = 0.2
    t_prime: float = 0.6
    t_double_prime: float = 0.05

    operating_point: CimtrOperatingPoint | None = solve_cimtr_operating_point(
        role, voltage_magnitude, voltage_angle, active_power, reactive_power,
        nominal_frequency_hz, resistance, x, x_prime, x_double_prime,
        t_prime, t_double_prime,
    )

    assert operating_point is not None
    if role == InductionMachineRole.GENERATOR:
        assert operating_point.omega > 1.0
    else:
        assert 0.0 < operating_point.omega < 1.0
    voltage_d: float = -voltage_magnitude * math.sin(voltage_angle)
    voltage_q: float = voltage_magnitude * math.cos(voltage_angle)
    residual: np.ndarray = _cimtr_equilibrium_residual(
        np.array((
            operating_point.ir, operating_point.ii,
            operating_point.epr, operating_point.epi,
            operating_point.eppr, operating_point.eppi,
            operating_point.omega,
        ), dtype=np.float64),
        voltage_d, voltage_q, active_power, role, nominal_frequency_hz,
        resistance, x, x_prime, x_double_prime, t_prime, t_double_prime,
    )
    assert np.max(np.abs(residual)) <= 1.0e-7
    assert operating_point.active_power == pytest.approx(active_power, abs=1.0e-7)
    assert operating_point.reactive_power + (
        operating_point.q_adjustment * voltage_magnitude ** 2
    ) == pytest.approx(reactive_power, abs=1.0e-7)
    electromagnetic_torque: float = (
        operating_point.eppr * operating_point.ir
        + operating_point.eppi * operating_point.ii
    )
    if role == InductionMachineRole.GENERATOR:
        expected_torque: float = -electromagnetic_torque
    else:
        expected_torque = electromagnetic_torque / operating_point.omega
    assert operating_point.torque_reference == pytest.approx(expected_torque)


@pytest.mark.parametrize(
    ('role', 'active_power', 'reactive_power'),
    (
        (InductionMachineRole.GENERATOR, 1.0, 0.2),
        (InductionMachineRole.MOTOR, 1.0, 0.2),
    ),
)
def test_cimtr_paper_absorbed_current_maps_to_native_power_signs(
        role: InductionMachineRole,
        active_power: float,
        reactive_power: float,
) -> None:
    """Check paper absorbed-current stator equations against native signs.

    :param role: Generator injection or motor absorption convention.
    :param active_power: Positive power magnitude on the machine base.
    :param reactive_power: Positive power magnitude on the machine base.
    :return: None.
    """
    voltage_magnitude: float = 0.8
    voltage_angle: float = 0.4
    resistance: float = 0.015
    x_double_prime: float = 0.2
    operating_point: CimtrOperatingPoint | None = solve_cimtr_operating_point(
        role, voltage_magnitude, voltage_angle, active_power, reactive_power,
        60.0, resistance, 3.0, 0.3, x_double_prime, 0.6, 0.05,
    )

    assert operating_point is not None
    voltage_d: float = -voltage_magnitude * math.sin(voltage_angle)
    voltage_q: float = voltage_magnitude * math.cos(voltage_angle)
    paper_id: float = -operating_point.ir
    paper_iq: float = -operating_point.ii
    paper_electrical_power: float = -(
        voltage_d * paper_id + voltage_q * paper_iq
    )
    paper_reactive_power: float = -(
        voltage_q * paper_id - voltage_d * paper_iq
    )

    assert voltage_d == pytest.approx(
        operating_point.eppr + resistance * paper_id - x_double_prime * paper_iq,
    )
    assert voltage_q == pytest.approx(
        operating_point.eppi + resistance * paper_iq + x_double_prime * paper_id,
    )
    if role == InductionMachineRole.GENERATOR:
        assert paper_electrical_power == pytest.approx(-active_power)
        assert paper_reactive_power == pytest.approx(-operating_point.reactive_power)
    else:
        assert paper_electrical_power == pytest.approx(active_power)
        assert paper_reactive_power == pytest.approx(operating_point.reactive_power)


def test_cimtr_operating_point_rejects_unsupported_parameters() -> None:
    """Reject invalid two-cage data before attempting a numerical solve."""
    operating_point: CimtrOperatingPoint | None = solve_cimtr_operating_point(
        InductionMachineRole.GENERATOR, 0.8, 0.4, 1.0, 0.2, 60.0,
        0.015, 3.0, 0.3, 0.0, 0.6, 0.05,
    )
    assert operating_point is None
