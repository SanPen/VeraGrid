# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 frequency response and active-power order from PSS/E 35.2 §17.1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Dera1ActivePowerSettings:
    """Store DERA1 frequency and active-power control parameters."""

    __slots__ = (
        'trf', 'tp', 'ddn', 'dup', 'fdbd1', 'fdbd2', 'femax', 'femin',
        'pmax', 'pmin', 'dpmax', 'dpmin', 'tpord', 'kpg', 'kig',
        'initial_frequency_deviation',
        'initial_active_power',
    )

    def __init__(
            self,
            trf: float = 0.02,
            tp: float = 0.02,
            ddn: float = 0.0,
            dup: float = 0.0,
            fdbd1: float = 0.0,
            fdbd2: float = 0.0,
            femax: float = 1.0,
            femin: float = -1.0,
            pmax: float = 1.0,
            pmin: float = 0.0,
            dpmax: float = 1.0,
            dpmin: float = -1.0,
            tpord: float = 0.02,
            kpg: float = 0.0,
            kig: float = 0.0,
            initial_frequency_deviation: float = 0.0,
            initial_active_power: float = 0.0,
    ) -> None:
        """Store the source parameters and solved initial operating point.

        :param trf: Frequency measurement time constant in seconds.
        :param tp: Active-power measurement time constant in seconds.
        :param ddn: Over-frequency droop gain.
        :param dup: Under-frequency droop gain.
        :param fdbd1: Lower frequency deadband edge, nonpositive pu.
        :param fdbd2: Upper frequency deadband edge, nonnegative pu.
        :param femax: Upper frequency-control error limit.
        :param femin: Lower frequency-control error limit.
        :param pmax: Maximum active-power order.
        :param pmin: Minimum active-power order.
        :param dpmax: Maximum upward active-power ramp in pu/s.
        :param dpmin: Minimum downward active-power ramp in pu/s.
        :param tpord: Active-power order lag time in seconds.
        :param kpg: Proportional active-power controller gain.
        :param kig: Integral active-power controller gain.
        :param initial_frequency_deviation: Solved frequency deviation in pu.
        :param initial_active_power: Solved active-power order in pu.
        :return: None.
        """
        self.trf: float = trf
        self.tp: float = tp
        self.ddn: float = ddn
        self.dup: float = dup
        self.fdbd1: float = fdbd1
        self.fdbd2: float = fdbd2
        self.femax: float = femax
        self.femin: float = femin
        self.pmax: float = pmax
        self.pmin: float = pmin
        self.dpmax: float = dpmax
        self.dpmin: float = dpmin
        self.tpord: float = tpord
        self.kpg: float = kpg
        self.kig: float = kig
        self.initial_frequency_deviation: float = initial_frequency_deviation
        self.initial_active_power: float = initial_active_power


def build_dera1_active_power_template(
        vf: VarFactory,
        name: str = 'DERA1 active power',
        settings: Dera1ActivePowerSettings | None = None,
        frequency_control: bool = True,
) -> RmsModelTemplate:
    """Build DERA1's frequency-response and active-power order path.

    The block follows the PSS/E diagram through the `Pord` output, including
    the dPmax/dPmin ramp state before the Tpord lag.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model-component name.
    :param settings: Source parameters and solved initialization point.
    :param frequency_control: True enables frequency response.
    :return: Controller with frequency deviation and Pref inputs.
    :raises ValueError: Invalid settings or initialization point.
    """
    selected: Dera1ActivePowerSettings = (
        Dera1ActivePowerSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.trf, selected.tp, selected.ddn, selected.dup,
        selected.fdbd1, selected.fdbd2, selected.femax, selected.femin,
        selected.pmax, selected.pmin, selected.dpmax, selected.dpmin,
        selected.tpord, selected.kpg,
        selected.kig, selected.initial_frequency_deviation,
        selected.initial_active_power,
    )
    if not isinstance(frequency_control, bool):
        raise ValueError('DERA1 FreqFlag must be Boolean')
    elif not all(math.isfinite(value) for value in values):
        raise ValueError('DERA1 active-power settings must be finite')
    elif min(selected.trf, selected.tp, selected.tpord, selected.ddn,
             selected.dup, selected.kpg, selected.kig) < 0.0:
        raise ValueError('DERA1 times and gains must be nonnegative')
    elif selected.dpmax <= 0.0 or selected.dpmin >= 0.0:
        raise ValueError('DERA1 power ramp rates must straddle zero')
    elif selected.fdbd1 > 0.0 or selected.fdbd2 < 0.0:
        raise ValueError('DERA1 frequency deadband must contain zero')
    elif selected.femin > selected.femax or selected.pmin > selected.pmax:
        raise ValueError('DERA1 controller and power limits are reversed')
    elif not selected.pmin <= selected.initial_active_power <= selected.pmax:
        raise ValueError('DERA1 initial active power is outside its limits')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    frequency: Var = control.input(
        'FrequencyDeviationPu', Const(selected.initial_frequency_deviation),
    )
    power_reference: Var = control.input(
        'ActivePowerReferencePu', Const(selected.initial_active_power),
    )
    active_power_order: Var = vf.add_var(name='ActivePowerOrderPu_' + name)
    frequency_time: Var = control.parameter('TRF', selected.trf)
    power_measurement_time: Var = control.parameter('TP', selected.tp)
    frequency_filter: Var = control.lag(
        'FilteredFrequencyDeviationPu', frequency, frequency_time, selected.trf,
        Const(selected.initial_frequency_deviation),
    )
    filtered_power: Var = control.lag(
        'FilteredPowerOrderPu', active_power_order, power_measurement_time,
        selected.tp, Const(selected.initial_active_power),
    )

    # The deadband output is zero inside its asymmetric band and tracks the
    # excess deviation outside it, matching the DERA1 frequency-control diagram.
    lower_deadband: Var = control.parameter('FDBD1', selected.fdbd1)
    upper_deadband: Var = control.parameter('FDBD2', selected.fdbd2)
    frequency_error: Expr = frequency_filter
    frequency_error = (
        frequency_error
        - lower_deadband * sym.heaviside(lower_deadband - frequency_filter)
        - upper_deadband * sym.heaviside(frequency_filter - upper_deadband)
    )
    droop_down: Var = control.parameter('DDN', selected.ddn)
    droop_up: Var = control.parameter('DUP', selected.dup)
    droop: Expr = (
        - droop_down * frequency_error * sym.heaviside(frequency_error)
        - droop_up * frequency_error * sym.heaviside(-frequency_error)
    )
    lower_error: Var = control.parameter('FEMIN', selected.femin)
    upper_error: Var = control.parameter('FEMAX', selected.femax)
    limited_error: Expr = sym.hard_sat(
        power_reference - filtered_power + droop, lower_error, upper_error,
    )
    proportional_gain: Var = control.parameter('KPG', selected.kpg)
    integral_gain: Var = control.parameter('KIG', selected.kig)
    initial_integrator: float = selected.initial_active_power
    integral: Var = vf.add_var(name='FrequencyPowerIntegral_' + name)
    control.differential(
        integral, integral_gain * limited_error, Const(initial_integrator),
    )
    power_limit_low: Var = control.parameter('PMIN', selected.pmin)
    power_limit_high: Var = control.parameter('PMAX', selected.pmax)
    controller_output: Expr = sym.hard_sat(
        integral + proportional_gain * limited_error,
        power_limit_low, power_limit_high,
    )
    if frequency_control:
        selected_order_demand: Expr = controller_output
    else:
        selected_order_demand = power_reference
    rate_limited_order: Var = vf.add_var(name='RateLimitedPowerCommandPu_' + name)
    rate_tracking_time: Const = Const(0.001)
    rate_limited_derivative: Expr = sym.hard_sat(
        (selected_order_demand - rate_limited_order) / rate_tracking_time,
        Const(selected.dpmin), Const(selected.dpmax),
    )
    control.differential(
        rate_limited_order, rate_limited_derivative,
        Const(selected.initial_active_power),
    )
    order_demand: Expr = rate_limited_order
    order_time: Var = control.parameter('TPORD', selected.tpord)
    control.lag(
        'ActivePowerOrderPu', order_demand, order_time, selected.tpord,
        Const(selected.initial_active_power), power_limit_low, power_limit_high,
        output=active_power_order,
    )
    return control.finish(
        (active_power_order,),
        'DERA1 filtered frequency response and active-power order through Pord',
    )
