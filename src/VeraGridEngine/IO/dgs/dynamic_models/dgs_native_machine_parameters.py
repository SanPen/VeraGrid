# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
"""Decode exact PowerFactory machine rows for native block construction."""

from __future__ import annotations

import math
from typing import Iterable, List, Tuple

from VeraGridEngine.IO.dgs.dgs_objects import ElmSym, TypSym
from VeraGridEngine.IO.dgs.dynamic_models.dgs_adapter_block_from_native_dgs import DgsElmSymMachineParameters
from VeraGridEngine.enumerations import SynchronousMachineSpeedVariationMode


def _open_circuit_time_constant(
        short_circuit_time: float,
        numerator_reactance: float,
        denominator_reactance: float,
) -> float:
    """Convert a short-circuit time constant to its open-circuit value.

    :param short_circuit_time: Exported short-circuit time in seconds.
    :param numerator_reactance: Reactance before the associated transient.
    :param denominator_reactance: Reactance after the associated transient.
    :return: Open-circuit time, or zero for an inactive circuit.
    """
    if short_circuit_time > 0.0 and denominator_reactance > 0.0:
        return short_circuit_time * numerator_reactance / denominator_reactance
    else:
        return 0.0


def _aligned_saturation_points(
        coordinates: Iterable[float | None],
        values: Iterable[float | None],
) -> Tuple[Tuple[float, ...], Tuple[float, ...]]:
    """Keep aligned finite points from an exported saturation curve.

    :param coordinates: Exported voltage coordinates.
    :param values: Corresponding excitation values.
    :return: Aligned coordinates and values usable by the physical builder.
    """
    result_coordinates: List[float] = list()
    result_values: List[float] = list()
    coordinate: float | None
    value: float | None
    for coordinate, value in zip(coordinates, values):
        if coordinate is None or value is None:
            pass
        elif math.isfinite(float(coordinate)) and math.isfinite(float(value)):
            result_coordinates.append(float(coordinate))
            result_values.append(float(value))
        else:
            pass
    return tuple(result_coordinates), tuple(result_values)


def build_dgs_elmsym_machine_parameters(
        source_machine: ElmSym,
        source_type: TypSym,
        operating_power_factor: float,
) -> DgsElmSymMachineParameters:
    """Decode the exact machine and type rows into physical parameters.

    :param source_machine: Native machine instance owning the dynamic model.
    :param source_type: Exact type referenced by the machine instance.
    :param operating_power_factor: Fallback for an absent rated power factor.
    :return: Parameters consumed by the native synchronous-machine builder.
    """
    # Preserve curve alignment before converting machine time constants and bases.
    d_voltage: Tuple[float, ...]
    d_excitation: Tuple[float, ...]
    q_voltage: Tuple[float, ...]
    q_excitation: Tuple[float, ...]
    acceleration_time: float
    speed_mode: SynchronousMachineSpeedVariationMode
    d_voltage, d_excitation = _aligned_saturation_points(
        source_type.saturation_voltage_points,
        source_type.saturation_excitation_points,
    )
    q_voltage, q_excitation = _aligned_saturation_points(
        source_type.saturation_q_voltage_points,
        source_type.saturation_q_excitation_points,
    )
    if source_type.calculated_tag is not None and float(source_type.calculated_tag) > 0.0:
        acceleration_time = float(source_type.calculated_tag)
    elif source_type.tag is not None:
        acceleration_time = float(source_type.tag)
    else:
        acceleration_time = 0.0
    speed_mode_raw: int = int(source_type.speed_variation_mode or 0)
    if speed_mode_raw == 1:
        speed_mode = SynchronousMachineSpeedVariationMode.Considered
    elif speed_mode_raw == 2:
        speed_mode = SynchronousMachineSpeedVariationMode.PartiallyNeglected
    else:
        speed_mode = SynchronousMachineSpeedVariationMode.Neglected
    rated_power_factor: float = abs(float(source_type.cosn))
    if rated_power_factor <= 0.0:
        rated_power_factor = abs(float(operating_power_factor))
    else:
        pass
    excitation_current_base: float = float(source_machine.excitation_current_base or 1.0)
    excitation_voltage_base_ratio: float = float(source_machine.excitation_voltage_base_ratio or 1.0)
    return DgsElmSymMachineParameters(
        Snom=float(source_type.sgn),
        rated_power_factor=rated_power_factor,
        Rs=float(source_type.rstr),
        Xd=float(source_type.xd),
        Xq=float(source_type.xq),
        Xd_prime=float(source_type.xds),
        Xq_prime=float(source_type.xqs),
        Xd_2prime=float(source_type.xdss),
        Xq_2prime=float(source_type.xqss),
        Xl=float(source_type.xl),
        Td0_prime=_open_circuit_time_constant(float(source_type.tds), float(source_type.xd), float(source_type.xds)),
        Tq0_prime=_open_circuit_time_constant(float(source_type.tqs), float(source_type.xq), float(source_type.xqs)),
        Td0_2prime=_open_circuit_time_constant(float(source_type.tdss), float(source_type.xds), float(source_type.xdss)),
        Tq0_2prime=_open_circuit_time_constant(
            float(source_type.tqss),
            float(source_type.xq if float(source_type.tqs) <= 0.0 else source_type.xqs),
            float(source_type.xqss),
        ),
        rms_acceleration_time_constant=acceleration_time,
        rms_dpu=float(source_type.dpu or 0.0),
        rms_dkd=float(source_type.dkd or 0.0),
        rms_dpe=float(source_type.dpe or 0.0),
        rms_rotor_coupling_reactance_d=float(source_type.xrl or 0.0),
        rms_rotor_coupling_reactance_q=float(source_type.xrlq),
        rms_td_prime_short_circuit=float(source_type.tds),
        rms_tq_prime_short_circuit=float(source_type.tqs),
        rms_td_2prime_short_circuit=float(source_type.tdss),
        rms_tq_2prime_short_circuit=float(source_type.tqss),
        rms_excitation_current_base=max(1.0e-12, excitation_current_base),
        rms_excitation_voltage_base_ratio=max(1.0e-12, excitation_voltage_base_ratio),
        rms_excitation_gain=0.0,
        rms_rated_field_voltage=float(source_machine.rated_field_voltage or 0.0),
        rms_saturation_curve_type=(
            -1 if int(source_type.satur) == 0 else int(source_type.isat or 0)
        ),
        rms_saturation_axis_mode=int(source_type.isat_salient or 0),
        rms_saturation_smoothing_factor=float(source_type.saturation_smoothing_factor or 0.0),
        rms_speed_variation_mode=speed_mode,
        rms_saturation_sg10=float(source_type.sg10 or 0.0),
        rms_saturation_sg12=float(source_type.sg12 or 0.0),
        rms_saturation_sg10q=float(source_type.sg10q or 0.0),
        rms_saturation_sg12q=float(source_type.sg12q or 0.0),
        rms_saturation_voltage_points=d_voltage,
        rms_saturation_excitation_points=d_excitation,
        rms_saturation_q_voltage_points=q_voltage,
        rms_saturation_q_excitation_points=q_excitation,
    )


