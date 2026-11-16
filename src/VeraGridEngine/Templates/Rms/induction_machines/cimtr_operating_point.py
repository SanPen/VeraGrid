# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Steady-state initialization for PSS/E CIMTR induction machines."""
from __future__ import annotations

import math

import numpy as np
from scipy.optimize import OptimizeResult, root

from VeraGridEngine.enumerations import InductionMachineRole


class CimtrOperatingPoint:
    """Store solved CIMTR flux, current, speed, torque, and Q adjustment."""

    __slots__ = (
        'omega', 'epr', 'epi', 'eppr', 'eppi', 'ir', 'ii',
        'active_power', 'reactive_power', 'torque_reference', 'q_adjustment',
    )

    def __init__(
            self, omega: float, epr: float, epi: float, eppr: float,
            eppi: float, ir: float, ii: float, active_power: float,
            reactive_power: float, torque_reference: float,
            q_adjustment: float,
    ) -> None:
        """Store one converged steady-state point.

        :param omega: Rotor speed in per unit.
        :param epr: d-axis transient rotor flux voltage.
        :param epi: q-axis transient rotor flux voltage.
        :param eppr: d-axis subtransient rotor flux voltage.
        :param eppi: q-axis subtransient rotor flux voltage.
        :param ir: d-axis stator current in per unit.
        :param ii: q-axis stator current in per unit.
        :param active_power: Source-role active power in per unit.
        :param reactive_power: Source-role reactive power in per unit.
        :param torque_reference: Constant mechanical/load torque reference.
        :param q_adjustment: Shunt susceptance on machine base in per unit.
        """
        self.omega: float = omega
        self.epr: float = epr
        self.epi: float = epi
        self.eppr: float = eppr
        self.eppi: float = eppi
        self.ir: float = ir
        self.ii: float = ii
        self.active_power: float = active_power
        self.reactive_power: float = reactive_power
        self.torque_reference: float = torque_reference
        self.q_adjustment: float = q_adjustment


def _cimtr_equilibrium_residual(
        values: np.ndarray,
        voltage_d: float,
        voltage_q: float,
        active_power_target: float,
        role: InductionMachineRole,
        nominal_frequency_hz: float,
        resistance: float,
        x: float,
        x_prime: float,
        x_double_prime: float,
        t_prime: float,
        t_double_prime: float,
) -> np.ndarray:
    """Evaluate the seven source steady-state equations for the root solve.

    :param values: d/q currents, four flux voltages, and rotor speed.
    :param voltage_d: Terminal d-axis voltage in the PSS/E network frame.
    :param voltage_q: Terminal q-axis voltage in the PSS/E network frame.
    :param active_power_target: Positive generation or motor consumption.
    :param role: Generator or motor power sign convention.
    :param nominal_frequency_hz: System frequency in hertz.
    :param resistance: Stator resistance in per unit.
    :param x: Synchronous reactance in per unit.
    :param x_prime: Transient reactance in per unit.
    :param x_double_prime: Subtransient reactance in per unit.
    :param t_prime: Transient time constant in seconds.
    :param t_double_prime: Subtransient time constant in seconds.
    :return: State derivatives, stator voltage residuals, and active-power residual.
    """
    ir: float = float(values[0])
    ii: float = float(values[1])
    epr: float = float(values[2])
    epi: float = float(values[3])
    eppr: float = float(values[4])
    eppi: float = float(values[5])
    omega: float = float(values[6])
    slip: float = 1.0 - omega
    omega_base: float = 2.0 * math.pi * nominal_frequency_hz
    d_epr: float = omega_base * slip * epi - (
        epr + (x - x_prime) * ii
    ) / t_prime
    d_epi: float = -omega_base * slip * epr - (
        epi - (x - x_prime) * ir
    ) / t_prime
    d_eppr: float = d_epr - omega_base * slip * (epi - eppi) - (
        (eppr - epr) + (x_prime - x_double_prime) * ii
    ) / t_double_prime
    d_eppi: float = d_epi + omega_base * slip * (epr - eppr) - (
        (eppi - epi) - (x_prime - x_double_prime) * ir
    ) / t_double_prime
    stator_d: float = voltage_d - eppr + resistance * ir - x_double_prime * ii
    stator_q: float = voltage_q - eppi + resistance * ii + x_double_prime * ir
    motor_active_power: float = voltage_d * ir + voltage_q * ii
    if role == InductionMachineRole.GENERATOR:
        calculated_active_power: float = -motor_active_power
    else:
        calculated_active_power = motor_active_power

    # Divide derivative residuals by synchronous frequency to keep solver scales aligned.
    return np.array((
        d_epr / omega_base, d_epi / omega_base,
        d_eppr / omega_base, d_eppi / omega_base,
        stator_d, stator_q,
        calculated_active_power - active_power_target,
    ), dtype=np.float64)


def solve_cimtr_operating_point(
        role: InductionMachineRole,
        voltage_magnitude: float,
        voltage_angle: float,
        active_power_target: float,
        reactive_power_target: float,
        nominal_frequency_hz: float,
        resistance: float,
        x: float,
        x_prime: float,
        x_double_prime: float,
        t_prime: float,
        t_double_prime: float,
        torque_exponent: float = 1.0,
) -> CimtrOperatingPoint | None:
    """Solve source flux equilibrium and the PSS/E Mvar-difference adjustment.

    Active power determines rotor slip; reactive-power difference is represented
    by the source model's hidden shunt. Saturation and single-cage reductions
    must be rejected by the caller before using this two-cage solver.

    :param role: Generator or motor source convention.
    :param voltage_magnitude: Solved terminal voltage magnitude in per unit.
    :param voltage_angle: Solved terminal angle in radians.
    :param active_power_target: Positive generation or motor consumption on machine base.
    :param reactive_power_target: Positive generation or motor consumption on machine base.
    :param nominal_frequency_hz: PSS/E system frequency in hertz.
    :param resistance: Stator resistance in per unit.
    :param x: Synchronous reactance in per unit.
    :param x_prime: Transient reactance in per unit.
    :param x_double_prime: Subtransient reactance in per unit.
    :param t_prime: Transient time constant in seconds.
    :param t_double_prime: Subtransient time constant in seconds.
    :param torque_exponent: CIMTR2/4 source D torque exponent.
    :return: Converged machine point or ``None`` when no physical root is found.
    """
    parameters: tuple[float, ...] = (
        voltage_magnitude, voltage_angle, active_power_target,
        reactive_power_target, nominal_frequency_hz, resistance, x,
        x_prime, x_double_prime, t_prime, t_double_prime, torque_exponent,
    )
    valid_role: bool = (
        role == InductionMachineRole.GENERATOR
        or role == InductionMachineRole.MOTOR
    )
    valid_input: bool = (
        all(math.isfinite(value) for value in parameters)
        and voltage_magnitude > 0.0 and active_power_target > 0.0
        and nominal_frequency_hz > 0.0 and resistance >= 0.0
        and x > x_prime > x_double_prime > 0.0
        and t_prime > 0.0 and t_double_prime > 0.0
        and torque_exponent >= 0.0
    )
    if not valid_role or not valid_input:
        result: CimtrOperatingPoint | None = None
    else:
        voltage_d: float = -voltage_magnitude * math.sin(voltage_angle)
        voltage_q: float = voltage_magnitude * math.cos(voltage_angle)
        motor_power_target: float = active_power_target
        motor_reactive_target: float = reactive_power_target
        if role == InductionMachineRole.GENERATOR:
            motor_power_target = -active_power_target
            motor_reactive_target = -reactive_power_target
        else:
            pass
        voltage_square: float = voltage_magnitude * voltage_magnitude
        initial_ir: float = (
            voltage_d * motor_power_target + voltage_q * motor_reactive_target
        ) / voltage_square
        initial_ii: float = (
            voltage_q * motor_power_target - voltage_d * motor_reactive_target
        ) / voltage_square
        initial_eppr: float = voltage_d + resistance * initial_ir - x_double_prime * initial_ii
        initial_eppi: float = voltage_q + resistance * initial_ii + x_double_prime * initial_ir
        if role == InductionMachineRole.GENERATOR:
            speed_guesses: tuple[float, ...] = (1.01, 1.03, 1.05, 1.1, 1.2)
        else:
            speed_guesses = (0.99, 0.97, 0.94, 0.90, 0.85, 0.75, 0.60)
        solved: np.ndarray | None = None
        speed_guess: float
        for speed_guess in speed_guesses:
            initial_state: np.ndarray = np.array((
                initial_ir, initial_ii, initial_eppr, initial_eppi,
                initial_eppr, initial_eppi, speed_guess,
            ), dtype=np.float64)
            solution: OptimizeResult = root(
                _cimtr_equilibrium_residual,
                initial_state,
                args=(
                    voltage_d, voltage_q, active_power_target, role,
                    nominal_frequency_hz, resistance, x, x_prime,
                    x_double_prime, t_prime, t_double_prime,
                ),
                method='hybr',
                tol=1.0e-10,
            )
            solution_values: np.ndarray = np.asarray(solution.x, dtype=np.float64)
            residual_values: np.ndarray = _cimtr_equilibrium_residual(
                solution_values, voltage_d, voltage_q, active_power_target,
                role, nominal_frequency_hz, resistance, x, x_prime,
                x_double_prime, t_prime, t_double_prime,
            )
            speed_value: float = float(solution_values[6])
            speed_valid: bool = (
                speed_value > 1.0
                if role == InductionMachineRole.GENERATOR
                else 0.0 < speed_value < 1.0
            )
            converged: bool = (
                solution.success and np.all(np.isfinite(solution_values))
                and np.all(np.isfinite(residual_values))
                and float(np.max(np.abs(residual_values))) <= 1.0e-7
                and speed_valid
            )
            if converged:
                solved = solution_values
                break
            else:
                pass
        else:
            pass

        if solved is not None:
            omega: float = float(solved[6])
            ir: float = float(solved[0])
            ii: float = float(solved[1])
            epr: float = float(solved[2])
            epi: float = float(solved[3])
            eppr: float = float(solved[4])
            eppi: float = float(solved[5])
            motor_active_power: float = voltage_d * ir + voltage_q * ii
            motor_reactive_power: float = voltage_q * ir - voltage_d * ii
            electromagnetic_torque: float = eppr * ir + eppi * ii
            if role == InductionMachineRole.GENERATOR:
                active_power: float = -motor_active_power
                reactive_power: float = -motor_reactive_power
                torque_reference: float = -electromagnetic_torque
            else:
                active_power = motor_active_power
                reactive_power = motor_reactive_power
                torque_reference = electromagnetic_torque / omega ** torque_exponent
            q_adjustment: float = (
                reactive_power_target - reactive_power
            ) / voltage_square
            finite_result: tuple[float, ...] = (
                omega, epr, epi, eppr, eppi, ir, ii, active_power,
                reactive_power, torque_reference, q_adjustment,
            )
            if all(math.isfinite(value) for value in finite_result):
                result = CimtrOperatingPoint(
                    finite_result[0], finite_result[1], finite_result[2],
                    finite_result[3], finite_result[4], finite_result[5],
                    finite_result[6], finite_result[7], finite_result[8],
                    finite_result[9], finite_result[10],
                )
            else:
                result = None
        else:
            result = None
    return result
