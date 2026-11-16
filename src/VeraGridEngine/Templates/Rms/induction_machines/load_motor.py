# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES steady-state helpers for shared one- and two-cage induction equations."""

import numpy as np

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.auxiliary_functions import (
    build_induction_machine,
)
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import BinOp, Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Utils.procedural_logic import delay, flipflop, pickup_dropoff
from VeraGridEngine.enumerations import (
    InductionMachineRole,
    VarPowerFlowReferenceType,
)


def evaluate_induction_machine_at_speed(
        speed: float,
        voltage_d: float,
        voltage_q: float,
        resistance: float,
        synchronous_reactance: float,
        transient_reactance: float,
        subtransient_reactance: float,
        transient_time: float,
        subtransient_time: float,
        frequency_hz: float,
        single_cage: bool = False,
) -> tuple[float, float, float, float, float, float, float, float, float] | None:
    """Solve the steady induction equations for one motor speed.

    :param speed: Per-unit rotor speed on synchronous base.
    :param voltage_d: Motor-frame d-axis terminal voltage.
    :param voltage_q: Motor-frame q-axis terminal voltage.
    :param resistance: Stator resistance in motor-base per unit.
    :param synchronous_reactance: Synchronous leakage reactance.
    :param transient_reactance: Transient reactance.
    :param subtransient_reactance: Subtransient reactance.
    :param transient_time: Open-circuit transient time constant.
    :param subtransient_time: Open-circuit subtransient time constant.
    :param frequency_hz: Nominal system frequency.
    :param single_cage: Use the source-defined one-cage reduction.
    :return: Fluxes, currents, electromagnetic torque, and P/Q, or ``None`` if singular.
    """
    slip: float = 1.0 - speed
    omega_base: float = 2.0 * np.pi * frequency_hz
    transient_denominator: float = max(transient_time, 1.0e-12)
    subtransient_denominator: float = max(subtransient_time, 1.0e-12)
    reactance_difference: float = synchronous_reactance - transient_reactance
    cage_difference: float = transient_reactance - subtransient_reactance
    matrix: np.ndarray
    right_hand_side: np.ndarray
    if single_cage:
        matrix = np.zeros((4, 4), dtype=np.float64)
        right_hand_side = np.zeros(4, dtype=np.float64)
        matrix[0, 0] = -1.0 / transient_denominator
        matrix[0, 1] = omega_base * slip
        matrix[0, 3] = -reactance_difference / transient_denominator
        matrix[1, 0] = -omega_base * slip
        matrix[1, 1] = -1.0 / transient_denominator
        matrix[1, 2] = reactance_difference / transient_denominator
        matrix[2, 0] = -1.0
        matrix[2, 2] = resistance
        matrix[2, 3] = -transient_reactance
        right_hand_side[2] = -voltage_d
        matrix[3, 1] = -1.0
        matrix[3, 2] = transient_reactance
        matrix[3, 3] = resistance
        right_hand_side[3] = -voltage_q
    else:
        matrix = np.zeros((6, 6), dtype=np.float64)
        right_hand_side = np.zeros(6, dtype=np.float64)
        # Rows one to four set both cage-flux derivatives to zero at this speed.
        matrix[0, 0] = -1.0 / transient_denominator
        matrix[0, 1] = omega_base * slip
        matrix[0, 5] = -reactance_difference / transient_denominator
        matrix[1, 0] = -omega_base * slip
        matrix[1, 1] = -1.0 / transient_denominator
        matrix[1, 4] = reactance_difference / transient_denominator
        matrix[2, 0] = -1.0 / transient_denominator + 1.0 / subtransient_denominator
        # Match the corrected shared-machine cage-slip signs in the RMS equation block.
        matrix[2, 1] = 0.0
        matrix[2, 2] = -1.0 / subtransient_denominator
        matrix[2, 3] = omega_base * slip
        matrix[2, 5] = (
            -reactance_difference / transient_denominator
            - cage_difference / subtransient_denominator
        )
        matrix[3, 0] = 0.0
        matrix[3, 1] = -1.0 / transient_denominator + 1.0 / subtransient_denominator
        matrix[3, 2] = -omega_base * slip
        matrix[3, 3] = -1.0 / subtransient_denominator
        matrix[3, 4] = (
            reactance_difference / transient_denominator
            + cage_difference / subtransient_denominator
        )
        # The last two rows are the shared induction-machine terminal circuit.
        matrix[4, 2] = -1.0
        matrix[4, 4] = resistance
        matrix[4, 5] = -subtransient_reactance
        right_hand_side[4] = -voltage_d
        matrix[5, 3] = -1.0
        matrix[5, 4] = subtransient_reactance
        matrix[5, 5] = resistance
        right_hand_side[5] = -voltage_q

    try:
        solution: np.ndarray = np.linalg.solve(matrix, right_hand_side)
    except np.linalg.LinAlgError:
        return None
    else:
        pass
    equation_residual: np.ndarray = matrix @ solution - right_hand_side
    equation_tolerance: float = 1.0e-9 * max(
        1.0,
        float(np.max(np.abs(right_hand_side))),
    )
    if (
            np.all(np.isfinite(solution))
            and float(np.max(np.abs(equation_residual))) <= equation_tolerance
    ):
        epr: float
        epi: float
        eppr: float
        eppi: float
        current_d: float
        current_q: float
        if single_cage:
            epr = float(solution[0])
            epi = float(solution[1])
            eppr = epr
            eppi = epi
            current_d = float(solution[2])
            current_q = float(solution[3])
        else:
            epr = float(solution[0])
            epi = float(solution[1])
            eppr = float(solution[2])
            eppi = float(solution[3])
            current_d = float(solution[4])
            current_q = float(solution[5])
        torque: float = eppr * current_d + eppi * current_q
        active_power: float = voltage_d * current_d + voltage_q * current_q
        reactive_power: float = voltage_q * current_d - voltage_d * current_q
        result: tuple[float, float, float, float, float, float, float, float, float] = (
            epr,
            epi,
            eppr,
            eppi,
            current_d,
            current_q,
            torque,
            active_power,
            reactive_power,
        )
    else:
        result = None
    return result


def solve_load_motor_operating_point(
        voltage_magnitude: float,
        voltage_angle: float,
        active_power_target: float,
        resistance: float,
        synchronous_reactance: float,
        transient_reactance: float,
        subtransient_reactance: float,
        transient_time: float,
        subtransient_time: float,
        frequency_hz: float,
        single_cage: bool = False,
        generator_mode: bool = False,
        reactive_power_target: float | None = None,
) -> tuple[float, float, float, float, float, float, float, float, float, float] | None:
    """Find a steady operating point for the shared induction-machine equations.

    :param voltage_magnitude: Solved terminal voltage magnitude.
    :param voltage_angle: Solved terminal voltage angle in radians.
    :param active_power_target: Active power in motor convention on machine MVA base.
    :param resistance: Stator resistance in machine-base per unit.
    :param synchronous_reactance: Synchronous leakage reactance.
    :param transient_reactance: Transient reactance.
    :param subtransient_reactance: Subtransient reactance.
    :param transient_time: Open-circuit transient time constant.
    :param subtransient_time: Open-circuit subtransient time constant.
    :param frequency_hz: Nominal system frequency.
    :param single_cage: Use the source-defined one-cage reduction.
    :param generator_mode: Search above synchronous speed for generating slip.
    :param reactive_power_target: Optional motor-convention reactive-power check.
    :return: Speed, four fluxes, currents, torque and P/Q, or ``None`` if no root exists.
    """
    voltage_d: float = -voltage_magnitude * float(np.sin(voltage_angle))
    voltage_q: float = voltage_magnitude * float(np.cos(voltage_angle))
    # Generating torque requires the high-speed side of the same induction equations.
    if generator_mode:
        speeds: np.ndarray = np.linspace(2.0, 1.0001, 1000, dtype=np.float64)
    else:
        speeds = np.linspace(0.01, 0.9999, 1000, dtype=np.float64)
    bracket_low: float | None = None
    bracket_high: float | None = None
    previous_speed: float | None = None
    previous_residual: float | None = None
    for speed_value in speeds[::-1]:
        speed: float = float(speed_value)
        operating_values: tuple[float, float, float, float, float, float, float, float, float] | None = (
            evaluate_induction_machine_at_speed(
                speed=speed,
                voltage_d=voltage_d,
                voltage_q=voltage_q,
                resistance=resistance,
                synchronous_reactance=synchronous_reactance,
                transient_reactance=transient_reactance,
                subtransient_reactance=subtransient_reactance,
                transient_time=transient_time,
                subtransient_time=subtransient_time,
                frequency_hz=frequency_hz,
                single_cage=single_cage,
            )
        )
        if operating_values is not None:
            residual: float = operating_values[7] - active_power_target
            if previous_residual is not None and previous_residual * residual <= 0.0:
                bracket_low = speed
                bracket_high = previous_speed
                previous_residual = residual
                break
            else:
                previous_speed = speed
                previous_residual = residual
        else:
            pass
    else:
        pass

    if bracket_low is not None and bracket_high is not None:
        low_speed: float = bracket_low
        high_speed: float = bracket_high
        low_values: tuple[float, float, float, float, float, float, float, float, float] | None = (
            evaluate_induction_machine_at_speed(
                speed=low_speed,
                voltage_d=voltage_d,
                voltage_q=voltage_q,
                resistance=resistance,
                synchronous_reactance=synchronous_reactance,
                transient_reactance=transient_reactance,
                subtransient_reactance=subtransient_reactance,
                transient_time=transient_time,
                subtransient_time=subtransient_time,
                frequency_hz=frequency_hz,
                single_cage=single_cage,
            )
        )
        low_residual: float = -active_power_target if low_values is None else low_values[7] - active_power_target
        for _ in range(64):
            middle_speed: float = 0.5 * (low_speed + high_speed)
            middle_values: tuple[float, float, float, float, float, float, float, float, float] | None = (
                evaluate_induction_machine_at_speed(
                    speed=middle_speed,
                    voltage_d=voltage_d,
                    voltage_q=voltage_q,
                    resistance=resistance,
                    synchronous_reactance=synchronous_reactance,
                    transient_reactance=transient_reactance,
                    subtransient_reactance=subtransient_reactance,
                    transient_time=transient_time,
                    subtransient_time=subtransient_time,
                    frequency_hz=frequency_hz,
                    single_cage=single_cage,
                )
            )
            if middle_values is not None:
                middle_residual: float = middle_values[7] - active_power_target
                if low_residual * middle_residual <= 0.0:
                    high_speed = middle_speed
                else:
                    low_speed = middle_speed
                    low_residual = middle_residual
            else:
                high_speed = middle_speed
        else:
            pass
        solved_speed: float = 0.5 * (low_speed + high_speed)
        final_values: tuple[float, float, float, float, float, float, float, float, float] | None = (
            evaluate_induction_machine_at_speed(
                speed=solved_speed,
                voltage_d=voltage_d,
                voltage_q=voltage_q,
                resistance=resistance,
                synchronous_reactance=synchronous_reactance,
                transient_reactance=transient_reactance,
                subtransient_reactance=subtransient_reactance,
                transient_time=transient_time,
                subtransient_time=subtransient_time,
                frequency_hz=frequency_hz,
                single_cage=single_cage,
            )
        )
        active_power_matches: bool = (
            final_values is not None
            and abs(final_values[7] - active_power_target)
            <= 1.0e-5 * max(1.0, abs(active_power_target))
        )
        # Active power chooses slip; reactive power independently validates that operating point.
        reactive_power_matches: bool = (
            reactive_power_target is None
            or (
                final_values is not None
                and abs(final_values[8] - reactive_power_target)
                <= 1.0e-5 * max(1.0, abs(reactive_power_target))
            )
        )
        if final_values is not None and active_power_matches and reactive_power_matches:
            result: tuple[float, float, float, float, float, float, float, float, float, float] | None = (
                solved_speed,
                final_values[0],
                final_values[1],
                final_values[2],
                final_values[3],
                final_values[4],
                final_values[5],
                final_values[6],
                final_values[7],
                final_values[8],
            )
        else:
            result = None
    else:
        result = None
    return result


def solve_asynchronous_generator_operating_point(
        voltage_magnitude: float,
        voltage_angle: float,
        active_power_target: float,
        reactive_power_target: float,
        resistance: float,
        synchronous_reactance: float,
        transient_reactance: float,
        subtransient_reactance: float,
        transient_time: float,
        subtransient_time: float,
        frequency_hz: float,
) -> tuple[float, float, float, float, float, float, float, float, float, float] | None:
    """Solve the fifth-order induction equilibrium for generator injection P and Q.

    :param voltage_magnitude: Solved terminal voltage magnitude.
    :param voltage_angle: Solved terminal voltage angle in radians.
    :param active_power_target: Generator active injection on its MVA base.
    :param reactive_power_target: Generator reactive injection on its MVA base.
    :param resistance: Stator resistance in machine-base per unit.
    :param synchronous_reactance: Synchronous reactance in machine-base per unit.
    :param transient_reactance: Transient reactance in machine-base per unit.
    :param subtransient_reactance: Subtransient reactance in machine-base per unit.
    :param transient_time: Open-circuit transient time constant.
    :param subtransient_time: Open-circuit subtransient time constant.
    :param frequency_hz: Nominal network frequency.
    :return: Speed, four fluxes, currents, torque and motor-convention P/Q, or ``None`` if
        active power has no generating-slip solution or its reactive power is inconsistent.
    """
    return solve_load_motor_operating_point(
        voltage_magnitude=voltage_magnitude,
        voltage_angle=voltage_angle,
        active_power_target=-active_power_target,
        resistance=resistance,
        synchronous_reactance=synchronous_reactance,
        transient_reactance=transient_reactance,
        subtransient_reactance=subtransient_reactance,
        transient_time=transient_time,
        subtransient_time=subtransient_time,
        frequency_hz=frequency_hz,
        generator_mode=True,
        reactive_power_target=-reactive_power_target,
    )


def seed_asynchronous_generator_operating_point(
        block: Block,
        name: str,
        operating_point: tuple[float, float, float, float, float, float, float, float, float, float],
        damping: float,
) -> bool:
    """Seed the shared generator-mode induction block at its solved equilibrium.

    :param block: CGMES asynchronous-machine equation block.
    :param name: Runtime name used by the machine variables.
    :param operating_point: Speed, four fluxes, currents, electromagnetic torque and P/Q.
    :param damping: Machine damping on its MVA base.
    :return: ``True`` if every state and generated algebraic output was located.
    """
    omega: Var | None = _find_load_motor_variable(block=block, name=f'OmegaPu_{name}')
    epr: Var | None = _find_load_motor_variable(block=block, name=f'EprPu_{name}')
    epi: Var | None = _find_load_motor_variable(block=block, name=f'EpiPu_{name}')
    eppr: Var | None = _find_load_motor_variable(block=block, name=f'EpprPu_{name}')
    eppi: Var | None = _find_load_motor_variable(block=block, name=f'EppiPu_{name}')
    current_d: Var | None = _find_load_motor_variable(block=block, name=f'IrPu_{name}')
    current_q: Var | None = _find_load_motor_variable(block=block, name=f'IiPu_{name}')
    electromagnetic_torque: Var | None = _find_load_motor_variable(block=block, name=f'TePu_{name}')
    generator_torque: Var | None = _find_load_motor_variable(block=block, name=f'TeGeneratorPu_{name}')
    active_power: Var | None = _find_load_motor_variable(block=block, name=f'PGenPu_{name}')
    reactive_power: Var | None = _find_load_motor_variable(block=block, name=f'QGenPu_{name}')
    torque_input: Var | None = _find_load_motor_variable(block=block, name=f'TmPu_{name}')
    required_variables: tuple[Var | None, ...] = (
        omega, epr, epi, eppr, eppi, current_d, current_q,
        electromagnetic_torque, generator_torque, active_power, reactive_power, torque_input,
    )
    if all(variable is not None for variable in required_variables):
        speed: float = operating_point[0]
        motor_torque: float = operating_point[7]
        # The shared equations use motor-convention electromagnetic torque and P/Q internally.
        generated_torque: float = -motor_torque
        shaft_torque: float = generated_torque + damping * (speed - 1.0)
        state_values: tuple[tuple[Var, float], ...] = (
            (omega, speed),
            (epr, operating_point[1]),
            (epi, operating_point[2]),
            (eppr, operating_point[3]),
            (eppi, operating_point[4]),
            (current_d, operating_point[5]),
            (current_q, operating_point[6]),
            (electromagnetic_torque, motor_torque),
            (generator_torque, generated_torque),
            (active_power, -operating_point[8]),
            (reactive_power, -operating_point[9]),
            (torque_input, shaft_torque),
        )
        if all(np.isfinite(value) for _, value in state_values):
            for variable, value in state_values:
                block.init_eqs[variable] = Const(value)
            seeded: bool = True
        else:
            seeded = False
    else:
        seeded = False
    return seeded


def seed_load_motor_operating_point(
        block: Block,
        name: str,
        operating_point: tuple[float, float, float, float, float, float, float, float, float, float],
        speed_exponent: float,
) -> bool:
    """Seed the motor states and algebraic outputs at its solved steady point.

    :param block: LoadMotor induction block to initialize.
    :param name: Runtime name used by its variables.
    :param operating_point: Speed, four fluxes, two currents, torque, and P/Q.
    :param speed_exponent: Canonical CGMES ``d`` mechanical-power exponent.
    :return: ``True`` when all required motor variables were found and seeded.
    """
    omega: Var | None = _find_load_motor_variable(block=block, name=f'OmegaPu_{name}')
    epr: Var | None = _find_load_motor_variable(block=block, name=f'EprPu_{name}')
    epi: Var | None = _find_load_motor_variable(block=block, name=f'EpiPu_{name}')
    eppr: Var | None = _find_load_motor_variable(block=block, name=f'EpprPu_{name}')
    eppi: Var | None = _find_load_motor_variable(block=block, name=f'EppiPu_{name}')
    current_d: Var | None = _find_load_motor_variable(block=block, name=f'IrPu_{name}')
    current_q: Var | None = _find_load_motor_variable(block=block, name=f'IiPu_{name}')
    electromagnetic_torque: Var | None = _find_load_motor_variable(block=block, name=f'TePu_{name}')
    load_torque: Var | None = _find_load_motor_variable(block=block, name=f'TLoadPu_{name}')
    active_power: Var | None = _find_load_motor_variable(block=block, name=f'PLoadPu_{name}')
    reactive_power: Var | None = _find_load_motor_variable(block=block, name=f'QLoadPu_{name}')
    torque_input: Var | None = _find_load_motor_variable(block=block, name=f'TLoad0Pu_{name}')
    required_variables: tuple[Var | None, ...] = (
        omega,
        epr,
        epi,
        current_d,
        current_q,
        electromagnetic_torque,
        load_torque,
        active_power,
        reactive_power,
        torque_input,
    )
    if all(variable is not None for variable in required_variables):
        speed: float = operating_point[0]
        torque: float = operating_point[7]
        torque_reference: float = torque / speed ** (speed_exponent - 1.0)
        state_values: list[tuple[Var, float]] = list((
            (omega, speed),
            (epr, operating_point[1]),
            (epi, operating_point[2]),
            (current_d, operating_point[5]),
            (current_q, operating_point[6]),
            (electromagnetic_torque, torque),
            (load_torque, torque),
            (active_power, operating_point[8]),
            (reactive_power, operating_point[9]),
        ))
        if eppr is not None:
            block.init_eqs[eppr] = Const(operating_point[3])
        else:
            pass
        if eppi is not None:
            block.init_eqs[eppi] = Const(operating_point[4])
        else:
            pass
        for variable, value in state_values:
            block.init_eqs[variable] = Const(value)
        torque_input_variable: Var = torque_input
        block.event_dict[torque_input_variable] = Const(torque_reference)
        retained_inputs: list[Var] = list()
        for input_variable in block.in_vars:
            if input_variable.uid == torque_input_variable.uid:
                pass
            else:
                retained_inputs.append(input_variable)
        block.in_vars = retained_inputs
        seeded: bool = True
    else:
        seeded = False
    return seeded


def seed_asynchronous_motor_operating_point(
        block: Block,
        name: str,
        operating_point: tuple[float, float, float, float, float, float, float, float, float, float],
        damping: float,
        seed_torque_input: bool,
) -> bool:
    """Seed the shared asynchronous-machine block in motor convention.

    :param block: CGMES asynchronous-machine equation block.
    :param name: Runtime name used by the machine variables.
    :param operating_point: Speed, four fluxes, currents, torque and motor P/Q.
    :param damping: Machine damping on its MVA base.
    :param seed_torque_input: Seed an unassociated torque port at equilibrium.
    :return: ``True`` when every required machine symbol was located and seeded.
    """
    omega: Var | None = _find_load_motor_variable(block=block, name=f'OmegaPu_{name}')
    epr: Var | None = _find_load_motor_variable(block=block, name=f'EprPu_{name}')
    epi: Var | None = _find_load_motor_variable(block=block, name=f'EpiPu_{name}')
    eppr: Var | None = _find_load_motor_variable(block=block, name=f'EpprPu_{name}')
    eppi: Var | None = _find_load_motor_variable(block=block, name=f'EppiPu_{name}')
    current_d: Var | None = _find_load_motor_variable(block=block, name=f'IrPu_{name}')
    current_q: Var | None = _find_load_motor_variable(block=block, name=f'IiPu_{name}')
    electromagnetic_torque: Var | None = _find_load_motor_variable(block=block, name=f'TePu_{name}')
    load_torque: Var | None = _find_load_motor_variable(block=block, name=f'TLoadPu_{name}')
    active_power: Var | None = _find_load_motor_variable(block=block, name=f'PLoadPu_{name}')
    reactive_power: Var | None = _find_load_motor_variable(block=block, name=f'QLoadPu_{name}')
    torque_input: Var | None = _find_load_motor_variable(block=block, name=f'TLoad0Pu_{name}')
    required_variables: tuple[Var | None, ...] = (
        omega, epr, epi, eppr, eppi, current_d, current_q, electromagnetic_torque,
        load_torque, active_power, reactive_power, torque_input,
    )
    if all(variable is not None for variable in required_variables):
        speed: float = operating_point[0]
        torque: float = operating_point[7]
        shaft_torque: float = torque - damping * (speed - 1.0)
        state_values: tuple[tuple[Var, float], ...] = (
            (omega, speed),
            (epr, operating_point[1]),
            (epi, operating_point[2]),
            (eppr, operating_point[3]),
            (eppi, operating_point[4]),
            (current_d, operating_point[5]),
            (current_q, operating_point[6]),
            (electromagnetic_torque, torque),
            (load_torque, shaft_torque),
            (active_power, operating_point[8]),
            (reactive_power, operating_point[9]),
        )
        if all(np.isfinite(value) for _, value in state_values) and np.isfinite(shaft_torque):
            for variable, value in state_values:
                block.init_eqs[variable] = Const(value)
            if seed_torque_input:
                block.init_eqs[torque_input] = Const(shaft_torque)
            else:
                pass
            seeded: bool = True
        else:
            seeded = False
    else:
        seeded = False
    return seeded


def _find_load_motor_variable(block: Block, name: str) -> Var | None:
    """Find one motor symbol by its exact CGMES runtime name.

    :param block: Motor block tree to inspect.
    :param name: Exact symbolic variable name.
    :return: Matching variable, or ``None`` when absent.
    """
    matching_variable: Var | None = None
    for candidate_block in block.get_all_blocks():
        candidate_variables: tuple[list[Var], ...] = (
            candidate_block.in_vars,
            candidate_block.out_vars,
            candidate_block.state_vars,
            candidate_block.algebraic_vars,
            list(candidate_block.event_dict.keys()),
        )
        for variables in candidate_variables:
            for candidate_variable in variables:
                if candidate_variable.name == name:
                    matching_variable = candidate_variable
                    break
                else:
                    pass
            if matching_variable is not None:
                break
            else:
                pass
        if matching_variable is not None:
            break
        else:
            pass
    else:
        pass
    return matching_variable


def build_load_motor_template(
        vfactory: VarFactory,
        name: str | None = None,
        role: InductionMachineRole = InductionMachineRole.MOTOR,
        nominal_frequency_hz: float = 50.0,
        single_cage: bool = False,
) -> RmsModelTemplate:
    """Build the CGMES one- or two-cage motor equations and retain RDF parameters.

    :param vfactory: Factory that owns all symbols.
    :param name: Optional runtime template name.
    :param role: Motor sign convention, kept explicit for adapter consistency.
    :param nominal_frequency_hz: Network electrical frequency in hertz.
    :param single_cage: Select the source-defined one-cage state reduction.
    :return: One- or two-cage induction motor with CGMES parameters mapped to RMS symbols.
    """
    template_name: str = 'LoadMotor' if name is None else name
    template: RmsModelTemplate = build_induction_machine(
        vf=vfactory,
        name=template_name,
        role=role,
    )
    frequency_variable: Var
    for frequency_variable in template.block.event_dict:
        if frequency_variable.name == f'FNomHz_{template_name}':
            template.block.event_dict[frequency_variable] = Const(nominal_frequency_hz)
        else:
            pass
    # The published LoadMotor parameters name synchronous/transient/subtransient reactances Ls/Lp/Lpp.
    rms_to_cgmes_names: tuple[tuple[str, str], ...] = (
        ('RaPu', 'ra'),
        ('XsPu', 'ls'),
        ('XpPu', 'lp'),
        ('XppPu', 'lpp'),
        ('Tp0', 'tpo'),
        ('Tpp0', 'tppo'),
        ('H', 'h'),
    )
    variables_to_replace: list[Var] = list()
    canonical_variables: list[Var] = list()
    equation_variable: Var
    for equation_variable in template.block.event_dict:
        for rms_name, cgmes_name in rms_to_cgmes_names:
            if equation_variable.name == f'{rms_name}_{template_name}':
                variables_to_replace.append(equation_variable)
                canonical_variables.append(
                    vfactory.add_var(f'LoadMotor.{cgmes_name}_{template_name}')
                )
            else:
                pass
    else:
        pass
    template.block.connect(
        vars_to_subs=variables_to_replace,
        incoming_vars=canonical_variables,
    )
    single_cage_applied: bool = False
    if single_cage:
        single_cage_applied = reduce_induction_machine_to_one_cage(
            block=template.block,
            name=template_name,
        )
    else:
        pass

    # Preserve motor share, loading factor, and undervoltage-breaker settings as RDF events.
    parameter_block: Block = Block(name=f'{template_name}_CGMES_parameters')
    loading_factor: Var = vfactory.add_var(f'LoadMotor.lfac_{template_name}')
    speed_exponent: Var = vfactory.add_var(f'LoadMotor.d_{template_name}')
    parameter_block.event_dict[loading_factor] = vfactory.add_const(value=None)
    parameter_block.event_dict[speed_exponent] = vfactory.add_const(value=None)
    for parameter_name in ('pfrac', 'vt', 'tv', 'tbkr'):
        parameter_variable: Var = vfactory.add_var(f'LoadMotor.{parameter_name}_{template_name}')
        parameter_block.event_dict[parameter_variable] = vfactory.add_const(value=None)
    template.block.children.insert(0, parameter_block)

    # Figure 179 uses terminal voltage to start/reset the undervoltage timer.
    terminal_voltage: Var = vfactory.add_var(
        f'Vm_{template_name}',
        reference=VarPowerFlowReferenceType.Vm,
    )
    terminal_angle: Var = vfactory.add_var(
        f'Va_{template_name}',
        reference=VarPowerFlowReferenceType.Va,
    )
    motor_d_axis_voltage: Var | None = None
    motor_q_axis_voltage: Var | None = None
    motor_torque_input: Var | None = None
    motor_input_variable: Var
    for motor_input_variable in template.block.in_vars:
        if motor_input_variable.name == f'VdPu_{template_name}':
            motor_d_axis_voltage = motor_input_variable
        elif motor_input_variable.name == f'VqPu_{template_name}':
            motor_q_axis_voltage = motor_input_variable
        elif motor_input_variable.name == f'TLoad0Pu_{template_name}':
            motor_torque_input = motor_input_variable
        else:
            pass
    else:
        pass
    if (
        motor_d_axis_voltage is not None
        and motor_q_axis_voltage is not None
        and motor_torque_input is not None
    ):
        template.block.in_vars = list((terminal_voltage, terminal_angle, motor_torque_input))
        template.block.algebraic_vars.extend((motor_d_axis_voltage, motor_q_axis_voltage))
        template.block.algebraic_eqs.extend((
            motor_d_axis_voltage + terminal_voltage * sym.sin(terminal_angle),
            motor_q_axis_voltage - terminal_voltage * sym.cos(terminal_angle),
        ))
        template.block.init_eqs[motor_d_axis_voltage] = (
            -terminal_voltage * sym.sin(terminal_angle)
        )
        template.block.init_eqs[motor_q_axis_voltage] = (
            terminal_voltage * sym.cos(terminal_angle)
        )
    else:
        pass
    timer_complete: Var = vfactory.add_var(f'UndervoltageTimerComplete_{template_name}')
    breaker_command: Var = vfactory.add_var(f'BreakerCommandDelayed_{template_name}')
    breaker_open: Var = vfactory.add_var(f'BreakerOpen_{template_name}')
    parameter_block.event_dict[timer_complete] = vfactory.add_const(value=0.0)
    parameter_block.event_dict[breaker_command] = vfactory.add_const(value=0.0)
    parameter_block.event_dict[breaker_open] = vfactory.add_const(value=0.0)
    voltage_threshold: Var | None = None
    pickup_delay: Var | None = None
    breaker_delay: Var | None = None
    parameter_variable: Var
    for parameter_variable in parameter_block.event_dict:
        if parameter_variable.name == f'LoadMotor.vt_{template_name}':
            voltage_threshold = parameter_variable
        elif parameter_variable.name == f'LoadMotor.tv_{template_name}':
            pickup_delay = parameter_variable
        elif parameter_variable.name == f'LoadMotor.tbkr_{template_name}':
            breaker_delay = parameter_variable
        else:
            pass
    else:
        pass
    if voltage_threshold is not None and pickup_delay is not None and breaker_delay is not None:
        template.block.procedural_logic.extend((
            pickup_dropoff(
                output=timer_complete,
                boolexpr=terminal_voltage < voltage_threshold,
                Tpick=pickup_delay,
                Tdrop=Const(0.0),
                name=f'{template_name}_undervoltage_timer',
            ),
            delay(
                input_expr=timer_complete,
                T=breaker_delay,
                output=breaker_command,
                name=f'{template_name}_breaker_delay',
            ),
            flipflop(
                boolset=breaker_command > Const(0.5),
                boolreset=Const(0.0) < Const(0.0),
                output=breaker_open,
                name=f'{template_name}_breaker_latch',
            ),
        ))
    else:
        pass

    # A tripped motor breaker removes this component's terminal power from the aggregate load.
    active_power: Var | None = None
    reactive_power: Var | None = None
    motor_algebraic_variable: Var
    for motor_algebraic_variable in template.block.algebraic_vars:
        if motor_algebraic_variable.name == f'PLoadPu_{template_name}':
            active_power = motor_algebraic_variable
        elif motor_algebraic_variable.name == f'QLoadPu_{template_name}':
            reactive_power = motor_algebraic_variable
        else:
            pass
    if active_power is not None and reactive_power is not None:
        active_equation_index: int | None = None
        reactive_equation_index: int | None = None
        for equation_index, algebraic_equation in enumerate(template.block.algebraic_eqs):
            if isinstance(algebraic_equation, BinOp) and algebraic_equation.left is active_power:
                active_equation_index = equation_index
            elif isinstance(algebraic_equation, BinOp) and algebraic_equation.left is reactive_power:
                reactive_equation_index = equation_index
            else:
                pass
        if active_equation_index is not None and reactive_equation_index is not None:
            active_power_expression: Expr = template.block.algebraic_eqs[active_equation_index].right
            reactive_power_expression: Expr = template.block.algebraic_eqs[reactive_equation_index].right
            breaker_closed: Expr = Const(1.0) - breaker_open
            gated_active_power: Expr = breaker_closed * active_power_expression
            gated_reactive_power: Expr = breaker_closed * reactive_power_expression
            template.block.algebraic_eqs[active_equation_index] = active_power - gated_active_power
            template.block.algebraic_eqs[reactive_equation_index] = reactive_power - gated_reactive_power
            template.block.init_eqs[active_power] = gated_active_power
            template.block.init_eqs[reactive_power] = gated_reactive_power
        else:
            pass
    else:
        pass
    template.block.external_mapping[VarPowerFlowReferenceType.Vm] = terminal_voltage
    template.block.external_mapping[VarPowerFlowReferenceType.Va] = terminal_angle
    template.block.out_vars.append(breaker_open)

    # Figure 179 specifies mechanical power as Pm0*speed**d; convert power to
    # torque with one division by speed and suppress the shared damping term.
    equation_variable: Var
    for equation_variable in template.block.event_dict:
        if equation_variable.name == f'Damp_{template_name}':
            template.block.event_dict[equation_variable] = vfactory.add_const(value=0.0)
        elif equation_variable.name == f'A_{template_name}':
            template.block.event_dict[equation_variable] = vfactory.add_const(value=0.0)
        elif equation_variable.name == f'B_{template_name}':
            template.block.event_dict[equation_variable] = vfactory.add_const(value=0.0)
        elif equation_variable.name == f'D_{template_name}':
            template.block.event_dict[equation_variable] = vfactory.add_const(value=1.0)
        elif equation_variable.name == f'E_{template_name}':
            template.block.event_dict[equation_variable] = (
                speed_exponent - Const(1.0)
            )
        else:
            pass
    else:
        pass

    # Lfac defines motor-base loading, not shaft torque; aggregate initialization supplies TLoad0.
    machine_order: str
    if single_cage_applied:
        machine_order = 'third-order one-cage'
    else:
        machine_order = 'fifth-order two-cage'
    template.comment = (
        f'CGMES LoadMotor {machine_order} induction-machine equations from the shared RMS realization. '
        'Figure 179 mechanical power follows speed**d, so shaft torque follows '
        'TLoad0*speed**(d-1). '
        'Bus Vm/Va drive the synchronous-frame motor voltages; the Figure 179 undervoltage timer '
        'and breaker latch use Vt, Tv, and Tbkr. Aggregate composition must consume BreakerOpen, '
        'allocate Pfrac, convert the motor base, initialize its operating point, and reconcile Q.'
    )
    if single_cage and not single_cage_applied:
        template.comment += ' The requested one-cage state reduction did not apply; this block is unsuitable for simulation.'
    else:
        pass
    return template


def reduce_induction_machine_to_one_cage(block: Block, name: str) -> bool:
    """Remove duplicated subtransient states from a one-cage LoadMotor.

    :param block: Shared induction-machine block adapted for CGMES.
    :param name: Unique model name used to identify its flux/reactance variables.
    :return: ``True`` when the state reduction was applied.
    """
    state_variables: dict[str, Var | None] = dict(
        (('EprPu', None), ('EpiPu', None), ('EpprPu', None), ('EppiPu', None))
    )
    reactance_variables: dict[str, Var | None] = dict(
        (('XpPu', None), ('XppPu', None))
    )
    canonical_reactance_names: dict[str, str] = dict((
        ('XpPu', f'LoadMotor.lp_{name}'),
        ('XppPu', f'LoadMotor.lpp_{name}'),
    ))
    candidate_variable: Var
    for candidate_variable in block.state_vars:
        for variable_name in state_variables:
            if candidate_variable.name == f'{variable_name}_{name}':
                state_variables[variable_name] = candidate_variable
            else:
                pass
    for candidate_variable in block.event_dict:
        for variable_name in reactance_variables:
            if (
                candidate_variable.name == f'{variable_name}_{name}'
                or candidate_variable.name == canonical_reactance_names[variable_name]
            ):
                reactance_variables[variable_name] = candidate_variable
            else:
                pass

    transient_d_axis: Var | None = state_variables['EprPu']
    transient_q_axis: Var | None = state_variables['EpiPu']
    subtransient_d_axis: Var | None = state_variables['EpprPu']
    subtransient_q_axis: Var | None = state_variables['EppiPu']
    transient_reactance: Var | None = reactance_variables['XpPu']
    subtransient_reactance: Var | None = reactance_variables['XppPu']
    if (
        transient_d_axis is not None
        and transient_q_axis is not None
        and subtransient_d_axis is not None
        and subtransient_q_axis is not None
        and transient_reactance is not None
        and subtransient_reactance is not None
    ):
        variable_substitutions: dict[Var, Var] = dict((
            (subtransient_d_axis, transient_d_axis),
            (subtransient_q_axis, transient_q_axis),
            (subtransient_reactance, transient_reactance),
        ))
        for equation_index in range(len(block.state_eqs)):
            block.state_eqs[equation_index] = block.state_eqs[equation_index].subs(
                variable_substitutions,
            )
        for equation_index in range(len(block.algebraic_eqs)):
            block.algebraic_eqs[equation_index] = block.algebraic_eqs[equation_index].subs(
                variable_substitutions,
            )
        for equation_index in range(len(block.differential_eqs)):
            block.differential_eqs[equation_index] = block.differential_eqs[equation_index].subs(
                variable_substitutions,
            )
        for equation_index in range(len(block.inequalities)):
            block.inequalities[equation_index] = block.inequalities[equation_index].subs(
                variable_substitutions,
            )

        eliminated_state_uids: set[int] = {
            subtransient_d_axis.uid,
            subtransient_q_axis.uid,
        }
        state_indices_to_remove: list[int] = list()
        for state_index in range(len(block.state_vars)):
            if block.state_vars[state_index].uid in eliminated_state_uids:
                state_indices_to_remove.append(state_index)
            else:
                pass
        for state_index in reversed(state_indices_to_remove):
            del block.state_vars[state_index]
            del block.state_eqs[state_index]

        retained_diff_vars: list[Var] = list()
        eliminated_diff_uids: set[int] = set()
        differential_variable: Var
        for differential_variable in block.diff_vars:
            if (
                differential_variable.base_var is not None
                and differential_variable.base_var.uid in eliminated_state_uids
            ):
                eliminated_diff_uids.add(differential_variable.uid)
            else:
                retained_diff_vars.append(differential_variable)
        block.diff_vars = retained_diff_vars

        retained_init_eqs: dict[Var, Expr | Const] = dict()
        for init_variable, init_expression in block.init_eqs.items():
            if init_variable.uid in eliminated_state_uids:
                pass
            else:
                retained_init_eqs[init_variable] = init_expression.subs(
                    variable_substitutions,
                )
        block.init_eqs = retained_init_eqs

        retained_diff_init_eqs: dict[Var, Expr | Const] = dict()
        for differential_variable, init_expression in block.diff_init_eqs.items():
            if differential_variable.uid in eliminated_diff_uids:
                pass
            else:
                retained_diff_init_eqs[differential_variable] = init_expression.subs(
                    variable_substitutions,
                )
        block.diff_init_eqs = retained_diff_init_eqs

        retained_seed_eqs: dict[Var, Expr | Const] = dict()
        for seed_variable, seed_expression in block.post_init_seed_eqs.items():
            if seed_variable.uid in eliminated_state_uids | eliminated_diff_uids:
                pass
            else:
                retained_seed_eqs[seed_variable] = seed_expression.subs(
                    variable_substitutions,
                )
        block.post_init_seed_eqs = retained_seed_eqs

        event_variable: Var
        for event_variable, event_expression in list(block.event_dict.items()):
            block.event_dict[event_variable] = event_expression.subs(variable_substitutions)
        for mode_variable, mode_expression in list(block.mode_dict.items()):
            block.mode_dict[mode_variable] = mode_expression.subs(variable_substitutions)
        for parameter_variable, parameter_expression in list(block.parameters.items()):
            block.parameters[parameter_variable] = parameter_expression.subs(variable_substitutions)
        return True
    else:
        return False
