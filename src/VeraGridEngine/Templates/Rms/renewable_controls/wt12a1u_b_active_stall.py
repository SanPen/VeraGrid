# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Continuous WT12A1U_B active-stall power path and voltage-delay lookup."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.procedural_logic import TimedPulseLogic
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Wt12a1uBSettings:
    """Store the fourteen ordered CONs of the 35.2 active-stall wrapper."""

    __slots__ = ('tr', 'rmax', 'rmin', 't0', 'pmin', 'pset', 'curve')

    def __init__(self, tr: float = .05, rmax: float = 1., rmin: float = 1.,
                 t0: float = .1, pmin: float = 0., pset: float = .8,
                 curve: tuple[tuple[float, float], ...] = ((-.3, 4.), (-.2, 3.),
                                                           (-.1, 2.), (.7, 1.))) -> None:
        """Store voltage filter, ramp rates, output lag and four duration bins.

        :param tr: Terminal-voltage filter time in seconds.
        :param rmax: Positive power-increase rate in per unit per second.
        :param rmin: Positive power-decrease rate magnitude in per unit per second.
        :param t0: Mechanical-power output lag in seconds.
        :param pmin: Minimum active-stall mechanical-power target in per unit.
        :param pset: Minimum initial power permitting active stall in per unit.
        :param curve: Four increasing (voltage, duration) pairs from the DYR.
        :return: None.
        """
        self.tr: float = tr
        self.rmax: float = rmax
        self.rmin: float = rmin
        self.t0: float = t0
        self.pmin: float = pmin
        self.pset: float = pset
        self.curve: tuple[tuple[float, float], ...] = curve


def build_wt12a1u_b_active_stall_template(
        vf: VarFactory, name: str = 'WT12A1U_B active stall',
        settings: Wt12a1uBSettings | None = None,
) -> RmsModelTemplate:
    """Build the sourced ramp/filter path with an open timed-switch input.

    The one-shot switch samples `DurationSeconds` when filtered voltage first
    crosses VT4 and initial power is at least PSET. It clears at the exact
    sampled expiration time, even if voltage remains low.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller name.
    :param settings: Source constants and voltage-duration pairs.
    :return: Stand-alone active-stall controller component.
    :raises ValueError: Invalid rates, times, power threshold or curve.
    """
    selected: Wt12a1uBSettings = Wt12a1uBSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.tr, selected.rmax, selected.rmin,
                                 selected.t0, selected.pmin, selected.pset)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('WT12A1U_B constants must be finite')
    elif min(selected.tr, selected.t0, selected.rmax, selected.rmin) < 0:
        raise ValueError('WT12A1U_B times and rates must be nonnegative')
    elif selected.rmax == 0 or selected.rmin == 0 or selected.pmin > selected.pset:
        raise ValueError('WT12A1U_B rates or power settings are invalid')
    elif len(selected.curve) != 4:
        raise ValueError('WT12A1U_B requires four voltage-duration pairs')
    else:
        pass
    index: int
    for index in range(4):
        voltage: float = selected.curve[index][0]
        duration: float = selected.curve[index][1]
        if not math.isfinite(voltage) or not math.isfinite(duration) or duration < 0:
            raise ValueError('WT12A1U_B curve values must be finite and nonnegative')
        elif index > 0 and voltage <= selected.curve[index - 1][0]:
            raise ValueError('WT12A1U_B voltages must increase')
        elif index > 0 and duration > selected.curve[index - 1][1]:
            raise ValueError('WT12A1U_B durations must decrease with voltage')
        else:
            pass

    control: ControlRealization = ControlRealization(vf, name)
    terminal_voltage: Var = control.input('TerminalVoltagePu', Const(1.))
    initial_power: Var = control.input('InitialMechanicalPowerPu', Const(0.))
    stall_switch: Var = vf.add_var('StallSwitchFlag_' + name)
    control.block.mode_dict[stall_switch] = Const(0.)
    tr: Var = control.parameter('TR', selected.tr)
    rmax: Var = control.parameter('RMAX', selected.rmax)
    rmin: Var = control.parameter('RMIN', selected.rmin)
    t0: Var = control.parameter('T0', selected.t0)
    pmin: Var = control.parameter('PMIN', selected.pmin)
    pset: Var = control.parameter('PSET', selected.pset)

    # The source rate limiter precedes the ramp integrator and uses the
    # lagged mechanical output for feedback.
    mechanical_power: Var = vf.add_var('MechanicalPowerPu_' + name)
    target: Expr = (Const(1.) - stall_switch) * initial_power + stall_switch * pmin
    ramp: Var = vf.add_var('PowerRampPu_' + name)
    control.differential(ramp, sym.hard_sat(target - mechanical_power, -rmin, rmax),
                         initial_power)
    control.lag('MechanicalPowerPu', ramp, t0, selected.t0, initial_power,
                output=mechanical_power)
    filtered_voltage: Var = control.lag('FilteredVoltagePu', terminal_voltage,
                                        tr, selected.tr, terminal_voltage)

    # EPRI's four voltage bins are steps: V<VT1 uses T1; VT3<=V<VT4
    # uses T4. Above VT4 the model's switch cannot be triggered.
    first_voltage: Var = control.parameter('VT1', selected.curve[0][0])
    first_delay: Var = control.parameter('T1', selected.curve[0][1])
    delay: Expr = first_delay
    prior_voltage: Var = first_voltage
    prior_delay: Var = first_delay
    for index in range(1, 4):
        next_voltage: Var = control.parameter('VT' + str(index + 1), selected.curve[index][0])
        next_delay: Var = control.parameter('T' + str(index + 1), selected.curve[index][1])
        delay = delay + (next_delay - prior_delay) * sym.heaviside(filtered_voltage - prior_voltage)
        prior_voltage = next_voltage
        prior_delay = next_delay
    delay = delay - prior_delay * sym.heaviside(filtered_voltage - prior_voltage)
    duration: Var = control.algebraic('DurationSeconds', delay, Const(0.))
    qualification: Var = control.algebraic(
        'QualifiedVoltageDip',
        sym.heaviside(prior_voltage - filtered_voltage)
        * (Const(1.) - sym.heaviside(pset - initial_power)),
        Const(0.),
    )
    control.block.procedural_logic.append(TimedPulseLogic(
        output_var_name=stall_switch.name,
        trigger_expr=qualification,
        duration_expr=duration,
        name='WT12A1U_B voltage-dip pulse ' + name,
    ))
    return control.finish((mechanical_power, filtered_voltage, duration, qualification,
                           stall_switch), 'Type 1/2 active-stall ramp and timed switch')
