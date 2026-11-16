# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Test-only reference interpreter of native EMT programs.

It evaluates a program exactly as the GSLV native evaluator does: DIFFERENTIAL
with GSLV's discretisation formulas and forward-mode tangents with GSLV's rules
(heaviside derivative 0, abs as sign, log and sqrt with 1e-15 guards,
power-constant special cases, divide zero-tangent branches).
"""

from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np
import numpy.typing as npt

from VeraGridEngine.enumerations import DynamicIntegrationMethod, EmtNativeOpcode
from VeraGridEngine.Simulations.EMT.problems.emt_native_program import EmtNativeProgram


class ProgramPoint:
    """
    Evaluation point of a program: states, parameters, histories, step and method.
    """

    __slots__ = ("states", "parameters", "history", "history2", "derivative_history", "h", "method")

    def __init__(self,
                 states: npt.NDArray[np.float64],
                 parameters: npt.NDArray[np.float64],
                 history: npt.NDArray[np.float64],
                 history2: npt.NDArray[np.float64],
                 derivative_history: npt.NDArray[np.float64],
                 h: float,
                 method: DynamicIntegrationMethod) -> None:
        """
        Store one evaluation point.

        :param states: Unknown vector (N).
        :param parameters: Full parameter vector [event | constant | literal].
        :param history: Previous unknowns (N).
        :param history2: Unknowns two steps back (N).
        :param derivative_history: Previous derivatives of the states (Ns).
        :param h: Step size.
        :param method: Integration method.
        """
        self.states: npt.NDArray[np.float64] = states
        self.parameters: npt.NDArray[np.float64] = parameters
        self.history: npt.NDArray[np.float64] = history
        self.history2: npt.NDArray[np.float64] = history2
        self.derivative_history: npt.NDArray[np.float64] = derivative_history
        self.h: float = float(h)
        self.method: DynamicIntegrationMethod = method


def differential_value(point: ProgramPoint, state_index: int) -> float:
    """
    Evaluate GSLV's discretised derivative of one state.

    :param point: Evaluation point.
    :param state_index: State (unknown) index.
    :return: Discretised derivative.
    """
    x: float = float(point.states[state_index])
    xh: float = float(point.history[state_index])
    if point.method == DynamicIntegrationMethod.DaeTrapezoidal:
        return 2.0 * (x - xh) / point.h - float(point.derivative_history[state_index])
    elif point.method == DynamicIntegrationMethod.DaeBackEuler:
        return (x - xh) / point.h
    elif point.method == DynamicIntegrationMethod.DaeBDF2:
        return 1.5 * (x - xh) / point.h - 0.5 * (xh - float(point.history2[state_index])) / point.h
    else:
        raise ValueError("Unsupported integration method")


def _differential_coefficient(point: ProgramPoint) -> float:
    """
    Return the tangent coefficient of DIFFERENTIAL for the point's method.

    :param point: Evaluation point.
    :return: 2/h, 1/h or 1.5/h.
    """
    if point.method == DynamicIntegrationMethod.DaeTrapezoidal:
        return 2.0 / point.h
    elif point.method == DynamicIntegrationMethod.DaeBackEuler:
        return 1.0 / point.h
    else:
        return 1.5 / point.h


def _evaluate_lane(program: EmtNativeProgram, group: int, lane: int, point: ProgramPoint, seed_slot: int) -> Tuple[List[float], List[float]]:
    """
    Evaluate one lane: primal values and, when seed_slot >= 0, tangents for that runtime slot.

    :param program: Native program.
    :param group: Group index.
    :param lane: Lane index.
    :param point: Evaluation point.
    :param seed_slot: Runtime slot seeded with 1, or -1 for primal only.
    :return: Primal and tangent value of every instruction.
    """
    field: List[int] = program.get_groups()[10 * group:10 * group + 10].tolist()
    lane_count: int = field[2]
    instructions: npt.NDArray[np.int32] = program.get_instructions()
    literals: npt.NDArray[np.float64] = program.get_instruction_literals()
    runtime_map: npt.NDArray[np.int32] = program.get_runtime_map()
    parameter_map: npt.NDArray[np.int32] = program.get_parameter_map()
    primal: List[float] = list()
    tangent: List[float] = list()
    local: int
    for local in range(field[1]):
        index: int = field[0] + local
        opcode: int = int(instructions[4 * index])
        first: int = int(instructions[4 * index + 1])
        second: int = int(instructions[4 * index + 2])
        value: float = 0.0
        derivative: float = 0.0
        if opcode == int(EmtNativeOpcode.CONSTANT):
            value = float(literals[index])
        elif opcode == int(EmtNativeOpcode.RUNTIME):
            value = float(point.states[int(runtime_map[field[4] + first * lane_count + lane])])
            derivative = 1.0 if first == seed_slot else 0.0
        elif opcode == int(EmtNativeOpcode.DIFFERENTIAL):
            value = differential_value(point, int(runtime_map[field[4] + first * lane_count + lane]))
            derivative = _differential_coefficient(point) if first == seed_slot else 0.0
        elif opcode == int(EmtNativeOpcode.PARAMETER):
            value = float(point.parameters[int(parameter_map[field[6] + first * lane_count + lane])])
        elif opcode == int(EmtNativeOpcode.ADD):
            value = primal[first] + primal[second]
            derivative = tangent[first] + tangent[second]
        elif opcode == int(EmtNativeOpcode.SUBTRACT):
            value = primal[first] - primal[second]
            derivative = tangent[first] - tangent[second]
        elif opcode == int(EmtNativeOpcode.MULTIPLY):
            value = primal[first] * primal[second]
            derivative = tangent[first] * primal[second] + primal[first] * tangent[second]
        elif opcode == int(EmtNativeOpcode.DIVIDE):
            value = primal[first] / primal[second]
            if tangent[first] == 0.0 and tangent[second] == 0.0:
                derivative = 0.0
            elif tangent[second] == 0.0:
                derivative = tangent[first] / primal[second]
            elif tangent[first] == 0.0:
                derivative = -primal[first] * tangent[second] / (primal[second] * primal[second])
            else:
                derivative = (tangent[first] * primal[second] - primal[first] * tangent[second]) / (primal[second] * primal[second])
        elif opcode == int(EmtNativeOpcode.POWER_CONSTANT):
            exponent: float = float(literals[index])
            value = math.pow(primal[first], exponent)
            if exponent == 1.0:
                derivative = tangent[first]
            elif exponent == 2.0:
                derivative = 2.0 * primal[first] * tangent[first]
            else:
                derivative = exponent * math.pow(primal[first], exponent - 1.0) * tangent[first]
        elif opcode == int(EmtNativeOpcode.POWER):
            value = math.pow(primal[first], primal[second])
            derivative = math.pow(primal[first], primal[second]) * (tangent[second] * math.log(primal[first]) + primal[second] * tangent[first] / primal[first])
        elif opcode == int(EmtNativeOpcode.NEGATE):
            value = -primal[first]
            derivative = -tangent[first]
        elif opcode == int(EmtNativeOpcode.SIN):
            value = math.sin(primal[first])
            derivative = math.cos(primal[first]) * tangent[first]
        elif opcode == int(EmtNativeOpcode.COS):
            value = math.cos(primal[first])
            derivative = -math.sin(primal[first]) * tangent[first]
        elif opcode == int(EmtNativeOpcode.EXP):
            value = math.exp(primal[first])
            derivative = math.exp(primal[first]) * tangent[first]
        elif opcode == int(EmtNativeOpcode.LOG):
            value = math.log(primal[first])
            derivative = tangent[first] / (primal[first] + 1.0e-15)
        elif opcode == int(EmtNativeOpcode.SQRT):
            value = math.sqrt(primal[first])
            derivative = 0.5 * tangent[first] / (math.sqrt(primal[first]) + 1.0e-15)
        elif opcode == int(EmtNativeOpcode.ABSOLUTE):
            value = abs(primal[first])
            sign: float = 1.0 if primal[first] > 0.0 else (-1.0 if primal[first] < 0.0 else 0.0)
            derivative = sign * tangent[first]
        elif opcode == int(EmtNativeOpcode.HEAVISIDE):
            value = 1.0 if primal[first] > 0.0 else 0.0
        else:
            raise ValueError("Unknown opcode " + str(opcode))
        primal.append(value)
        tangent.append(derivative)
    return primal, tangent


def evaluate_program_residual(program: EmtNativeProgram, point: ProgramPoint) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Evaluate the residual of a program.

    :param program: Native program.
    :param point: Evaluation point.
    :return: Residual (N) and the largest absolute intermediate value of each row's lane.
    """
    n: int = program.get_n_unknowns()
    residual: npt.NDArray[np.float64] = np.zeros(n, dtype=np.float64)
    magnitude: npt.NDArray[np.float64] = np.zeros(n, dtype=np.float64)
    residual_map: npt.NDArray[np.int32] = program.get_residual_map()
    groups: npt.NDArray[np.int32] = program.get_groups()
    group: int
    for group in range(program.get_n_groups()):
        lane: int
        for lane in range(int(groups[10 * group + 2])):
            primal: List[float]
            tangent: List[float]
            primal, tangent = _evaluate_lane(program, group, lane, point, -1)
            row: int = int(residual_map[int(groups[10 * group + 8]) + lane])
            residual[row] = primal[-1]
            magnitude[row] = max(abs(value) for value in primal)
    return residual, magnitude


def evaluate_program_jacobian(program: EmtNativeProgram, point: ProgramPoint) -> Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    """
    Evaluate the dense Jacobian of a program by forward-mode tangents per runtime slot.

    :param program: Native program.
    :param point: Evaluation point.
    :return: Dense Jacobian (N x N) and the largest absolute intermediate tangent of each row's lane.
    """
    n: int = program.get_n_unknowns()
    jacobian: npt.NDArray[np.float64] = np.zeros((n, n), dtype=np.float64)
    magnitude: npt.NDArray[np.float64] = np.zeros(n, dtype=np.float64)
    residual_map: npt.NDArray[np.int32] = program.get_residual_map()
    runtime_map: npt.NDArray[np.int32] = program.get_runtime_map()
    groups: npt.NDArray[np.int32] = program.get_groups()
    group: int
    for group in range(program.get_n_groups()):
        lane_count: int = int(groups[10 * group + 2])
        runtime_begin: int = int(groups[10 * group + 4])
        runtime_slots: int = int(groups[10 * group + 5]) // lane_count
        lane: int
        for lane in range(lane_count):
            row: int = int(residual_map[int(groups[10 * group + 8]) + lane])
            slot: int
            for slot in range(runtime_slots):
                primal: List[float]
                tangent: List[float]
                primal, tangent = _evaluate_lane(program, group, lane, point, slot)
                column: int = int(runtime_map[runtime_begin + slot * lane_count + lane])
                jacobian[row, column] += tangent[-1]
                magnitude[row] = max(magnitude[row], max(abs(value) for value in tangent))
    return jacobian, magnitude
