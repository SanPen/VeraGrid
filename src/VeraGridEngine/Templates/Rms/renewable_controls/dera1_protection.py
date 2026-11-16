# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 timed voltage/frequency trip and recovery multipliers."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.Utils.procedural_logic import (
    DelayedThresholdLatchLogic,
    ResetOnRisingEdgeLogic,
)
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Dera1ProtectionSettings:
    """Store DERA1 protection thresholds and initialization conditions."""

    __slots__ = (
        'voltage_trip_enabled', 'frequency_trip_enabled', 'vl0', 'vl1', 'vh0',
        'vh1', 'tvl0', 'tvl1', 'tvh0', 'tvh1', 'vrfrac', 'fl', 'fh', 'tfl',
        'tfh', 'tv', 'vpr', 'initial_voltage', 'initial_frequency_hz',
    )

    def __init__(
            self,
            voltage_trip_enabled: bool = False,
            frequency_trip_enabled: bool = False,
            vl0: float = 0.0,
            vl1: float = 0.0,
            vh0: float = 2.0,
            vh1: float = 2.0,
            tvl0: float = 0.0,
            tvl1: float = 0.0,
            tvh0: float = 0.0,
            tvh1: float = 0.0,
            vrfrac: float = 0.0,
            fl: float = 57.0,
            fh: float = 63.0,
            tfl: float = 0.0,
            tfh: float = 0.0,
            tv: float = 0.02,
            vpr: float = 0.0,
            initial_voltage: float = 1.0,
            initial_frequency_hz: float = 60.0,
    ) -> None:
        """Store PSS/E protection settings and solved measurements.

        :param voltage_trip_enabled: VtripFlag selector.
        :param frequency_trip_enabled: FtripFlag selector.
        :param vl0: Low-voltage full-trip threshold.
        :param vl1: Low-voltage partial-trip threshold, at least vl0.
        :param vh0: High-voltage full-trip threshold.
        :param vh1: High-voltage partial-trip threshold, at most vh0.
        :param tvl0: Full low-voltage trip delay in seconds.
        :param tvl1: Partial low-voltage trip delay in seconds.
        :param tvh0: Full high-voltage trip delay in seconds.
        :param tvh1: Partial high-voltage trip delay in seconds.
        :param vrfrac: Fraction restored after a prolonged partial trip.
        :param fl: Low-frequency trip threshold in hertz.
        :param fh: High-frequency trip threshold in hertz.
        :param tfl: Low-frequency trip delay in seconds.
        :param tfh: High-frequency trip delay in seconds.
        :param tv: Trip-multiplier output lag time in seconds.
        :param vpr: Voltage below which frequency tripping is bypassed.
        :param initial_voltage: Solved terminal voltage in pu.
        :param initial_frequency_hz: Solved system frequency in hertz.
        :return: None.
        """
        self.voltage_trip_enabled: bool = voltage_trip_enabled
        self.frequency_trip_enabled: bool = frequency_trip_enabled
        self.vl0: float = vl0
        self.vl1: float = vl1
        self.vh0: float = vh0
        self.vh1: float = vh1
        self.tvl0: float = tvl0
        self.tvl1: float = tvl1
        self.tvh0: float = tvh0
        self.tvh1: float = tvh1
        self.vrfrac: float = vrfrac
        self.fl: float = fl
        self.fh: float = fh
        self.tfl: float = tfl
        self.tfh: float = tfh
        self.tv: float = tv
        self.vpr: float = vpr
        self.initial_voltage: float = initial_voltage
        self.initial_frequency_hz: float = initial_frequency_hz


def _build_voltage_recovery_curve(
        control: ControlRealization,
        name: str,
        voltage: Expr,
        lower_trip: float,
        upper_trip: float,
        recovery_fraction: float,
        initial_extreme: float,
        full_trip_normal: Var,
        partial_trip_normal: Var,
        enabled: bool,
) -> Var:
    """Build one source voltage multiplier using transformed low-side logic.

    :param control: DERA1 protection block being assembled.
    :param name: Unique low-side branch label.
    :param voltage: Voltage for undervoltage or negated voltage for overvoltage.
    :param lower_trip: Full-trip boundary in the transformed coordinate.
    :param upper_trip: Partial-trip boundary in the transformed coordinate.
    :param recovery_fraction: Source Vrfrac setting.
    :param initial_extreme: Initial value of Vmin or negated Vmax.
    :param full_trip_normal: Runtime latch output, one until full trip.
    :param partial_trip_normal: Runtime latch output, one until partial trip.
    :param enabled: True when source initialization permits this branch.
    :return: Voltage multiplier in [0, 1].
    """
    multiplier_name: str = name + 'Multiplier'
    if enabled:
        extreme: Var = control.parameter(name + 'Extreme', initial_extreme)
        counter: Expr = Const(1.0) - partial_trip_normal
        reset_condition = counter > Const(0.5)
        control.block.procedural_logic.append(ResetOnRisingEdgeLogic(
            target_var_name=extreme.name,
            reset_expr=reset_condition,
            value_expr=voltage,
            name=name + ' extreme capture',
        ))
        interval: Expr = sym.max(Const(upper_trip - lower_trip), Const(1e-9))
        raw_curve: Expr = sym.hard_sat(
            (voltage - Const(lower_trip)) / interval, Const(0.0), Const(1.0),
        )
        bounded_extreme: Expr = sym.hard_sat(
            extreme, Const(lower_trip), Const(upper_trip),
        )
        recovery_voltage: Expr = sym.min(voltage, Const(upper_trip))
        recovered_curve: Expr = sym.hard_sat(
            (bounded_extreme - Const(lower_trip)
             + Const(recovery_fraction) * (recovery_voltage - bounded_extreme))
            / interval,
            Const(0.0), Const(1.0),
        )
        selected_curve: Expr = (
            raw_curve * partial_trip_normal
            + recovered_curve * (Const(1.0) - partial_trip_normal)
        )
        above_full_trip: Expr = sym.heaviside(voltage - Const(lower_trip))
        multiplier: Var = control.algebraic(
            multiplier_name,
            selected_curve * above_full_trip * full_trip_normal,
            Const(1.0),
        )
    else:
        multiplier = control.algebraic(multiplier_name, Const(1.0), Const(1.0))
    return multiplier


def build_dera1_protection_template(
        vf: VarFactory,
        name: str = 'DERA1 protection',
        settings: Dera1ProtectionSettings | None = None,
) -> RmsModelTemplate:
    """Build DERA1 voltage recovery and frequency trip protection.

    Voltage timer expiration uses the shared exact-event latch; a rising-edge
    sampler captures Vmin/Vmax at partial-trip timer expiration.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model-component name.
    :param settings: PSS/E protection settings and solved measurements.
    :return: Controller with voltage and frequency inputs and trip multipliers.
    :raises ValueError: Invalid source thresholds or initialization conditions.
    """
    selected: Dera1ProtectionSettings = (
        Dera1ProtectionSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.vl0, selected.vl1, selected.vh0, selected.vh1,
        selected.tvl0, selected.tvl1, selected.tvh0, selected.tvh1,
        selected.vrfrac, selected.fl, selected.fh, selected.tfl,
        selected.tfh, selected.tv, selected.vpr, selected.initial_voltage,
        selected.initial_frequency_hz,
    )
    if not isinstance(selected.voltage_trip_enabled, bool) or not isinstance(selected.frequency_trip_enabled, bool):
        raise ValueError('DERA1 protection flags must be Boolean')
    elif not all(math.isfinite(value) for value in values):
        raise ValueError('DERA1 protection settings must be finite')
    elif selected.vl0 > selected.vl1 or selected.vh1 > selected.vh0:
        raise ValueError('DERA1 voltage protection thresholds are reversed')
    elif min(selected.tvl0, selected.tvl1, selected.tvh0, selected.tvh1,
             selected.tfl, selected.tfh, selected.tv) < 0.0:
        raise ValueError('DERA1 protection timers must be nonnegative')
    elif not 0.0 <= selected.vrfrac <= 1.0:
        raise ValueError('DERA1 Vrfrac must be in [0, 1]')
    elif selected.fl <= 0.0 or selected.fh <= selected.fl:
        raise ValueError('DERA1 frequency thresholds are invalid')
    elif selected.vpr < 0.0 or selected.initial_voltage <= 0.0 or selected.initial_frequency_hz <= 0.0:
        raise ValueError('DERA1 protection initialization is invalid')
    else:
        pass

    undervoltage_enabled: bool = (
        selected.voltage_trip_enabled
        and selected.initial_voltage >= max(selected.vl0, selected.vl1)
    )
    overvoltage_enabled: bool = (
        selected.voltage_trip_enabled
        and selected.initial_voltage <= min(selected.vh0, selected.vh1)
    )
    frequency_enabled: bool = (
        selected.frequency_trip_enabled
        and selected.fl <= selected.initial_frequency_hz <= selected.fh
    )

    control: ControlRealization = ControlRealization(vf, name)
    voltage: Var = control.input('FilteredTerminalVoltagePu', Const(selected.initial_voltage))
    frequency: Var = control.input('FilteredFrequencyHz', Const(selected.initial_frequency_hz))
    negative_voltage: Var = control.algebraic(
        'NegativeFilteredVoltagePu', -voltage, Const(-selected.initial_voltage),
    )
    negative_frequency: Var = control.algebraic(
        'NegativeFilteredFrequencyHz', -frequency,
        Const(-selected.initial_frequency_hz),
    )

    uv_full_normal: Var = control.parameter('UnderVoltageFullTripNormal', 1.0)
    uv_partial_normal: Var = control.parameter('UnderVoltagePartialTripNormal', 1.0)
    ov_full_normal: Var = control.parameter('OverVoltageFullTripNormal', 1.0)
    ov_partial_normal: Var = control.parameter('OverVoltagePartialTripNormal', 1.0)
    if undervoltage_enabled:
        control.block.procedural_logic.append(DelayedThresholdLatchLogic(
            negative_voltage.name, uv_full_normal.name, -selected.vl0,
            selected.tvl0, name=name + ' low-voltage full trip',
        ))
        control.block.procedural_logic.append(DelayedThresholdLatchLogic(
            negative_voltage.name, uv_partial_normal.name, -selected.vl1,
            selected.tvl1, name=name + ' low-voltage partial trip',
        ))
    else:
        pass
    if overvoltage_enabled:
        control.block.procedural_logic.append(DelayedThresholdLatchLogic(
            voltage.name, ov_full_normal.name, selected.vh0,
            selected.tvh0, name=name + ' high-voltage full trip',
        ))
        control.block.procedural_logic.append(DelayedThresholdLatchLogic(
            voltage.name, ov_partial_normal.name, selected.vh1,
            selected.tvh1, name=name + ' high-voltage partial trip',
        ))
    else:
        pass

    under_multiplier: Var = _build_voltage_recovery_curve(
        control, 'UnderVoltage', voltage, selected.vl0, selected.vl1,
        selected.vrfrac, selected.initial_voltage, uv_full_normal,
        uv_partial_normal, undervoltage_enabled,
    )
    over_multiplier: Var = _build_voltage_recovery_curve(
        control, 'OverVoltage', negative_voltage, -selected.vh0,
        -selected.vh1, selected.vrfrac, -selected.initial_voltage,
        ov_full_normal, ov_partial_normal, overvoltage_enabled,
    )
    voltage_multiplier: Var = control.algebraic(
        'VoltageTripMultiplier', under_multiplier * over_multiplier,
        Const(1.0),
    )

    frequency_low_normal: Var = control.parameter('LowFrequencyTripNormal', 1.0)
    frequency_high_normal: Var = control.parameter('HighFrequencyTripNormal', 1.0)
    if frequency_enabled:
        voltage_gate: Expr = sym.heaviside(voltage - Const(selected.vpr))
        low_safe_value: Const = Const(-2.0 * selected.fl)
        low_frequency_metric: Var = control.algebraic(
            'LowFrequencyTripMetricHz',
            voltage_gate * negative_frequency
            + (Const(1.0) - voltage_gate) * low_safe_value,
            low_safe_value,
        )
        high_frequency_metric: Var = control.algebraic(
            'HighFrequencyTripMetricHz',
            voltage_gate * frequency,
            Const(0.0),
        )
        control.block.procedural_logic.append(DelayedThresholdLatchLogic(
            low_frequency_metric.name, frequency_low_normal.name, -selected.fl,
            selected.tfl, name=name + ' low-frequency trip',
        ))
        control.block.procedural_logic.append(DelayedThresholdLatchLogic(
            high_frequency_metric.name, frequency_high_normal.name, selected.fh,
            selected.tfh, name=name + ' high-frequency trip',
        ))
    else:
        pass
    frequency_multiplier: Var = control.algebraic(
        'FrequencyTripMultiplier', frequency_low_normal * frequency_high_normal,
        Const(1.0),
    )
    combined_multiplier: Expr = voltage_multiplier * frequency_multiplier
    multiplier_time: Var = control.parameter('TV', selected.tv)
    trip_multiplier: Var = control.lag(
        'TripMultiplier', combined_multiplier, multiplier_time,
        selected.tv, Const(1.0),
    )
    return control.finish(
        (voltage_multiplier, frequency_multiplier, trip_multiplier),
        'DERA1 timed voltage recovery and frequency-trip multipliers',
    )
