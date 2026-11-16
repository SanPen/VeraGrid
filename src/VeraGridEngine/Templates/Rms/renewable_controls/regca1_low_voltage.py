# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REGCA1 converter current control and converged network boundary."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.renewable_controls.current_source_host import build_renewable_current_source_host
from VeraGridEngine.Utils.Symbolic.block import Block
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.enumerations import RmsProblemTypes, VarPowerFlowReferenceType


class Regca1LowVoltageSettings:
    """Store converter, LVPL, recovery, and high-voltage boundary settings."""

    __slots__ = ('tg', 'rrpwr', 'brkpt', 'zerox', 'lvpl1', 'lvpnt1', 'lvpnt0',
                 'tfltr', 'iqrmax', 'iqrmin', 'lvplsw', 'volim', 'iolim', 'khv', 'accel')

    def __init__(self, tg: float = .02, rrpwr: float = 10., brkpt: float = .9,
                 zerox: float = .4, lvpl1: float = 1.22, lvpnt1: float = .8,
                 lvpnt0: float = .4, tfltr: float = .02, iqrmax: float = 999.,
                 iqrmin: float = -999., lvplsw: bool = True,
                 volim: float = 1.1, iolim: float = -1.2, khv: float = .7,
                 accel: float = .4) -> None:
        """Store independently named physical settings.

        :param tg: Converter current lag, seconds.
        :param rrpwr: Maximum active-current rise rate, per unit per second.
        :param brkpt: Upper LVPL voltage breakpoint, per unit.
        :param zerox: Lower LVPL voltage breakpoint, per unit.
        :param lvpl1: Active-current ceiling at the upper breakpoint.
        :param lvpnt1: Voltage where active-current multiplier reaches one.
        :param lvpnt0: Voltage where active-current multiplier reaches zero.
        :param tfltr: Terminal-voltage filter time, seconds.
        :param iqrmax: Positive-Q recovery current-rate ceiling.
        :param iqrmin: Negative-Q recovery current-rate floor.
        :param lvplsw: Enable the filtered-voltage LVPL curve.
        :param volim: Terminal-voltage threshold for high-voltage current correction.
        :param iolim: Minimum reactive current at the network interface.
        :param khv: Overvoltage compensation gain.
        :param accel: Source network-iteration correction gain.
        :return: None.
        """
        self.tg: float = tg
        self.rrpwr: float = rrpwr
        self.brkpt: float = brkpt
        self.zerox: float = zerox
        self.lvpl1: float = lvpl1
        self.lvpnt1: float = lvpnt1
        self.lvpnt0: float = lvpnt0
        self.tfltr: float = tfltr
        self.iqrmax: float = iqrmax
        self.iqrmin: float = iqrmin
        self.lvplsw: bool = lvplsw
        self.volim: float = volim
        self.iolim: float = iolim
        self.khv: float = khv
        self.accel: float = accel


def build_regca1_low_voltage_template(
        vf: VarFactory,
        name: str = 'REGCA1 low-voltage converter',
        settings: Regca1LowVoltageSettings | None = None,
        problem_type: RmsProblemTypes = RmsProblemTypes.PowerBalanceVectorized,
) -> RmsModelTemplate:
    """Build the connected converter lag, LVPL and low-voltage current stages.

    The controller uses positive active/reactive current on generator MVA base.
    It stores converter currents and filtered terminal voltage when their times
    are positive; a zero voltage-filter time reduces algebraically. Reactive
    recovery limits use the initial reactive-power sign. High-voltage reactive
    current correction is algebraic and bounded by the remaining IOLIM range;
    ACCEL remains source iteration metadata and does not scale physical output.

    :param vf: Shared symbolic variable factory.
    :param name: Unique generator template name.
    :param settings: Converter settings; defaults provide a finite example.
    :param problem_type: Voltage coordinate system of the network problem.
    :return: Network-connected converter template with converged high-voltage management.
    :raises ValueError: Invalid physical settings or network formulation.
    """
    selected: Regca1LowVoltageSettings = Regca1LowVoltageSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.tg, selected.rrpwr, selected.brkpt,
                                 selected.zerox, selected.lvpl1, selected.lvpnt1,
                                 selected.lvpnt0, selected.tfltr, selected.iqrmax,
                                 selected.iqrmin, selected.volim, selected.iolim,
                                 selected.khv, selected.accel)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Converter settings must be finite')
    elif selected.tg < 0 or selected.tfltr < 0 or selected.rrpwr <= 0:
        raise ValueError('Converter lag and active-current rate are invalid')
    elif selected.tg == 0:
        # A finite current-rate limiter still needs memory when its lag vanishes.
        # The hybrid jump/ramp law is not represented by an algebraic reduction.
        raise ValueError('Zero converter time with finite rate limits is unsupported')
    elif selected.brkpt <= selected.zerox or selected.lvpnt1 <= selected.lvpnt0:
        raise ValueError('Converter voltage breakpoints must be ordered')
    elif selected.lvpl1 <= 0 or selected.iqrmax <= 0 or selected.iqrmin >= 0:
        raise ValueError('Converter current capabilities are invalid')
    elif (selected.volim <= 0 or selected.iolim >= 0 or selected.khv < 0
          or selected.accel <= 0 or selected.accel > 1):
        raise ValueError('High-voltage correction settings are invalid')
    elif not isinstance(selected.lvplsw, bool):
        raise ValueError('LVPL selection must be Boolean')
    else:
        pass

    # Reuse the network host so the controller sees the same live voltage,
    # power-flow initialization and machine/system MVA conversion as the host.
    template: RmsModelTemplate = build_renewable_current_source_host(
        vf=vf, name=name, problem_type=problem_type,
    )
    block: Block = template.block
    ip_order: Var = list(block.event_dict)[0]
    iq_order: Var = list(block.event_dict)[1]
    active_current: Var = block.out_vars[2]
    reactive_current: Var = block.out_vars[3]
    system_q: Var = block.external_mapping[VarPowerFlowReferenceType.Q]
    vm: Expr
    if problem_type in (RmsProblemTypes.CurrentBalance, RmsProblemTypes.Multilinear):
        vr: Var = block.external_mapping[VarPowerFlowReferenceType.Vr]
        vi: Var = block.external_mapping[VarPowerFlowReferenceType.Vi]
        vm = sym.sqrt(vr * vr + vi * vi)
    else:
        vm = block.external_mapping[VarPowerFlowReferenceType.Vm]

    # The initial Q sign is captured once from the solved power flow. A live Q
    # signal would switch the recovery bound during a voltage disturbance.
    initial_q: Var = vf.add_var('InitialReactivePower_' + name)
    block.event_dict[initial_q] = system_q
    tg: Var = vf.add_var('TG_' + name)
    tfltr: Var = vf.add_var('TFLTR_' + name)
    rrpwr: Var = vf.add_var('RRPWR_' + name)
    iqrmax: Var = vf.add_var('IQRMAX_' + name)
    iqrmin: Var = vf.add_var('IQRMIN_' + name)
    volim: Var = vf.add_var('VOLIM_' + name)
    iolim: Var = vf.add_var('IOLIM_' + name)
    khv: Var = vf.add_var('KHV_' + name)
    accel: Var = vf.add_var('ACCEL_' + name)
    block.event_dict[tg] = vf.add_const(selected.tg)
    block.event_dict[tfltr] = vf.add_const(selected.tfltr)
    block.event_dict[rrpwr] = vf.add_const(selected.rrpwr)
    block.event_dict[iqrmax] = vf.add_const(selected.iqrmax)
    block.event_dict[iqrmin] = vf.add_const(selected.iqrmin)
    block.event_dict[volim] = vf.add_const(selected.volim)
    block.event_dict[iolim] = vf.add_const(selected.iolim)
    block.event_dict[khv] = vf.add_const(selected.khv)
    block.event_dict[accel] = vf.add_const(selected.accel)

    filtered: Var = vf.add_var('FilteredVoltage_' + name)
    if selected.tfltr == 0:
        block.algebraic_vars.append(filtered)
        block.algebraic_eqs.append(filtered - vm)
    else:
        pass
    block.init_eqs[filtered] = vm

    # LVPL uses filtered voltage; the terminal multiplier below uses live
    # voltage. The two paths must remain distinct through a voltage fault.
    active_target: Expr = ip_order
    if selected.lvplsw:
        zerox: Var = vf.add_var('ZEROX_' + name)
        brkpt: Var = vf.add_var('BRKPT_' + name)
        lvpl1: Var = vf.add_var('LVPL1_' + name)
        block.event_dict[zerox] = vf.add_const(selected.zerox)
        block.event_dict[brkpt] = vf.add_const(selected.brkpt)
        block.event_dict[lvpl1] = vf.add_const(selected.lvpl1)
        lvpl: Expr = sym.hard_sat(lvpl1 * (filtered - zerox) / (brkpt - zerox),
                                  Const(0.), lvpl1)
        active_target = sym.min(ip_order, lvpl)
    else:
        pass
    lvpnt0: Var = vf.add_var('LVPNT0_' + name)
    lvpnt1: Var = vf.add_var('LVPNT1_' + name)
    block.event_dict[lvpnt0] = vf.add_const(selected.lvpnt0)
    block.event_dict[lvpnt1] = vf.add_const(selected.lvpnt1)
    multiplier: Expr = sym.hard_sat((vm - lvpnt0) / (lvpnt1 - lvpnt0),
                                    Const(0.), Const(1.))

    ip_lag: Var = vf.add_var('ConverterActiveCurrent_' + name)
    iq_lag: Var = vf.add_var('ConverterReactiveCurrent_' + name)
    raw_active_rate: Expr = (active_target - ip_lag) / tg
    # Recovery is bounded in the direction of the present current; at zero,
    # the requested direction chooses which of the two bounds applies.
    negative_current: Expr = sym.heaviside(-ip_lag)
    zero_current: Expr = Const(1.) - sym.heaviside(ip_lag) - negative_current
    negative_direction: Expr = negative_current + zero_current * sym.heaviside(-raw_active_rate)
    active_rate: Expr = (sym.min(raw_active_rate, rrpwr)
                         + negative_direction * (sym.max(raw_active_rate, -rrpwr)
                                                 - sym.min(raw_active_rate, rrpwr)))
    reactive_rate: Expr = (iq_order - iq_lag) / tg
    positive_initial_q: Expr = sym.heaviside(initial_q - Const(1e-9))
    negative_initial_q: Expr = sym.heaviside(-initial_q - Const(1e-9))
    recovery_rate: Expr = (reactive_rate
                           + positive_initial_q * (sym.min(reactive_rate, iqrmax) - reactive_rate)
                           + negative_initial_q * (sym.max(reactive_rate, iqrmin) - reactive_rate))
    block.state_vars.extend((ip_lag, iq_lag))
    block.diff_vars.extend((vf.add_diff_var('d_' + ip_lag.name, base_var=ip_lag),
                            vf.add_diff_var('d_' + iq_lag.name, base_var=iq_lag)))
    block.state_eqs.extend((active_rate, recovery_rate))
    block.init_eqs[ip_lag] = active_target
    block.init_eqs[iq_lag] = iq_order
    if selected.tfltr == 0:
        pass
    else:
        # Keep the PSS/E source order: active current, reactive current, voltage.
        block.state_vars.append(filtered)
        block.diff_vars.append(vf.add_diff_var('d_' + filtered.name, base_var=filtered))
        block.state_eqs.append((vm - filtered) / tfltr)
    # Khv defines the physical high-voltage current correction. Accel belongs
    # to the source network iteration and must not scale this converged output.
    correction: Var = vf.add_var('HighVoltageReactiveCorrection_' + name)
    correction_limit: Expr = sym.max(iq_lag - iolim, Const(0.))
    correction_request: Expr = khv * sym.max(vm - volim, Const(0.))
    correction_residual: Expr = correction - sym.hard_sat(
        correction_request, Const(0.), correction_limit,
    )
    block.algebraic_vars.append(correction)
    block.algebraic_eqs.append(correction_residual)
    block.init_eqs[correction] = Const(0.)
    block.algebraic_eqs[0] = active_current - ip_lag * multiplier
    block.algebraic_eqs[1] = reactive_current - (iq_lag - correction)
    template.comment = 'REGCA1 converter current control with converged high-voltage network correction'
    return template
