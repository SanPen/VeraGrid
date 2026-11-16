# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""IEEE ST10C static excitation system with parallel control paths."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Templates.Rms.excitation_systems.ac9c_rectifier_supply import _ac9c_fex_value
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
from VeraGridEngine.enumerations import DeviceType
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class St10cParameters:
    """Store the 25 PSS/E ST10C constants in source order."""

    __slots__ = (
        'tr', 'kr', 'tc1', 'tb1', 'tc2', 'tb2',
        'vrsmax', 'vrsmin',
        'vrmax', 'vrmin', 't1', 'kp', 'kc', 'ki', 'xl', 'thetap_rad', 'vbmax',
    )

    def __init__(
            self, tr: float = 0.01, kr: float = 500.0, tc1: float = 1.5,
            tb1: float = 12.5, tc2: float = 0.1, tb2: float = 0.1,
            vrsmax: float = 5.0,
            vrsmin: float = -5.0, vrmax: float = 10.0, vrmin: float = -8.7,
            t1: float = 0.004, kp: float = 1.0, kc: float = 0.01,
            ki: float = 0.0, xl: float = 0.0, thetap_rad: float = 0.0,
            vbmax: float = 1.5,
    ) -> None:
        """Validate and retain physical parameters.

        :param tr: Regulator input filter time in seconds.
        :param kr: Common regulator gain.
        :param tc1: AVR second-stage lead time.
        :param tb1: AVR second-stage lag time.
        :param tc2: AVR first-stage lead time.
        :param tb2: AVR first-stage lag time.
        :param vrsmax: PSS path regulator upper limit.
        :param vrsmin: PSS path regulator lower limit.
        :param vrmax: Main regulator upper limit.
        :param vrmin: Main regulator lower limit.
        :param t1: Rectifier bridge time constant.
        :param kp: Potential-source voltage gain.
        :param kc: Rectifier commutation loading factor.
        :param ki: Potential-source current gain.
        :param xl: Potential-source reactance.
        :param thetap_rad: Potential-source phase angle in radians.
        :param vbmax: Maximum available exciter voltage.
        :raises ValueError: A parameter is nonfinite or violates its bounds.
        """
        values: tuple[float, ...] = (
            tr, kr, tc1, tb1, tc2, tb2, vrsmax, vrsmin, vrmax, vrmin, t1, kp, kc, ki, xl,
            thetap_rad, vbmax,
        )
        times: tuple[float, ...] = (
            tr, tc1, tb1, tc2, tb2, t1,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError('ST10C constants must be finite')
        elif min(times) < 0.0 or kr <= 0.0 or kp <= 0.0 or vbmax <= 0.0:
            raise ValueError('ST10C times, regulator gain, and source limits are invalid')
        elif min(kc, ki, xl) < 0.0:
            raise ValueError('ST10C source coefficients must be nonnegative')
        elif vrmin >= vrmax or vrsmin >= vrsmax:
            raise ValueError('ST10C regulator limits must be ordered')
        else:
            pass
        self.tr: float = tr
        self.kr: float = kr
        self.tc1: float = tc1
        self.tb1: float = tb1
        self.tc2: float = tc2
        self.tb2: float = tb2
        self.vrsmax: float = vrsmax
        self.vrsmin: float = vrsmin
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.t1: float = t1
        self.kp: float = kp
        self.kc: float = kc
        self.ki: float = ki
        self.xl: float = xl
        self.thetap_rad: float = thetap_rad
        self.vbmax: float = vbmax


def build_st10c_template(
        vf: VarFactory, name: str | None = None,
        parameters: St10cParameters | None = None,
        sensed_voltage0: float = 1.0, field_current0: float = 1.0,
        field_voltage0: float = 1.0, terminal_voltage0: complex = 1.0 + 0.0j,
        terminal_current0: complex = 0.0 + 0.0j,
) -> RmsModelTemplate:
    """Build the ST10C AVR, limiter/PSS paths and terminal-fed rectifier.

    :param vf: Factory owning every symbolic variable.
    :param name: Optional unique template label.
    :param parameters: PSS/E physical constants.
    :param sensed_voltage0: Solved voltage measurement initial value.
    :param field_current0: Solved generator field current.
    :param field_voltage0: Solved generator field voltage.
    :param terminal_voltage0: Solved terminal voltage phasor.
    :param terminal_current0: Solved terminal current phasor.
    :return: Native ST10C template with named controller and phasor inputs.
    :raises ValueError: Initial values are nonfinite or outside capabilities.
    """
    label: str = 'ST10C' if name is None else name
    selected: St10cParameters = St10cParameters() if parameters is None else parameters
    initial_values: tuple[float, ...] = (
        sensed_voltage0, field_current0, field_voltage0,
        terminal_voltage0.real, terminal_voltage0.imag,
        terminal_current0.real, terminal_current0.imag,
    )
    if not all(math.isfinite(value) for value in initial_values):
        raise ValueError('ST10C initial operating point must be finite')
    elif sensed_voltage0 <= 0.0 or field_voltage0 < 0.0 or field_voltage0 > selected.vbmax:
        raise ValueError('ST10C initial voltage is outside its capability')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, label)
    time_filter: Var = control.parameter('TR', selected.tr)
    gain: Var = control.parameter('KR', selected.kr)
    avr_tc1: Var = control.parameter('TC1', selected.tc1)
    avr_tb1: Var = control.parameter('TB1', selected.tb1)
    avr_tc2: Var = control.parameter('TC2', selected.tc2)
    avr_tb2: Var = control.parameter('TB2', selected.tb2)
    vrmax: Var = control.parameter('VRMAX', selected.vrmax)
    vrmin: Var = control.parameter('VRMIN', selected.vrmin)
    vrsmax: Var = control.parameter('VRSMAX', selected.vrsmax)
    vrsmin: Var = control.parameter('VRSMIN', selected.vrsmin)
    bridge_time: Var = control.parameter('T1', selected.t1)
    kp: Var = control.parameter('KP', selected.kp)
    kc: Var = control.parameter('KC', selected.kc)
    ki: Var = control.parameter('KI', selected.ki)
    xl: Var = control.parameter('XL', selected.xl)
    phase: Var = control.parameter('THETAP', selected.thetap_rad)
    vbmax: Var = control.parameter('VBMAX', selected.vbmax)

    voltage: Var = control.input('VT', Const(abs(terminal_voltage0)))
    sensed: Var = control.lag('SensedVoltage', voltage, time_filter, selected.tr, Const(sensed_voltage0))
    reference: Var = control.input('VREF', Const(sensed_voltage0))
    stabilizer: Var = control.input('VS', Const(0.0))
    uel: Var = control.input('VUEL', Const(0.0))
    oel: Var = control.input('VOEL', Const(0.0))
    scl_sum: Var = control.input('VSCLSUM', Const(0.0))
    field_current: Var = control.input('IFD', Const(field_current0))

    error: Expr = reference - sensed + stabilizer + uel + oel + scl_sum
    avr_first: Var = control.lead_lag('AvrFirstLeadLag', error, avr_tc2, avr_tb2, selected.tc2, selected.tb2, Const(0.0))
    avr_second: Var = control.lead_lag('AvrSecondLeadLag', avr_first, avr_tc1, avr_tb1, selected.tc1, selected.tb1, Const(0.0))
    avr_selected: Expr = sym.min(sym.max(avr_second, vrmin / gain), vrmax / gain)
    vr_command: Var = control.algebraic(
        'RegulatorCommand', gain * avr_selected,
        Const(field_voltage0),
    )

    voltage_r: Var = control.input('VTR', Const(terminal_voltage0.real))
    voltage_i: Var = control.input('VTI', Const(terminal_voltage0.imag))
    current_r: Var = control.input('ITR', Const(terminal_current0.real))
    current_i: Var = control.input('ITI', Const(terminal_current0.imag))
    voltage_gain_r: Expr = kp * sym.cos(phase)
    voltage_gain_i: Expr = kp * sym.sin(phase)
    current_gain_r: Expr = ki + voltage_gain_r * xl
    current_gain_i: Expr = voltage_gain_i * xl
    source_r: Expr = (
        voltage_gain_r * voltage_r - voltage_gain_i * voltage_i
        - current_gain_r * current_i - current_gain_i * current_r
    )
    source_i: Expr = (
        voltage_gain_i * voltage_r + voltage_gain_r * voltage_i
        + current_gain_r * current_r - current_gain_i * current_i
    )
    source_magnitude: Expr = sym.sqrt(source_r * source_r + source_i * source_i)
    source_initial: float = abs(
        selected.kp * complex(math.cos(selected.thetap_rad), math.sin(selected.thetap_rad)) * terminal_voltage0
        + 1j * (
            selected.ki + selected.kp * complex(math.cos(selected.thetap_rad), math.sin(selected.thetap_rad)) * selected.xl
        ) * terminal_current0
    )
    loading_initial: float = selected.kc * field_current0 / max(source_initial, 1e-9)
    supply_initial: float = min(
        selected.vbmax,
        source_initial * _ac9c_fex_value(loading_initial),
    )
    if supply_initial <= 0.0:
        raise ValueError('ST10C terminal source cannot support the initial field voltage')
    else:
        pass
    regulator_error0: float = field_voltage0 / (supply_initial * selected.kr)
    control.block.init_eqs[reference] = Const(sensed_voltage0 + regulator_error0)
    control.block.init_eqs[avr_first] = Const(regulator_error0)
    control.block.init_eqs[avr_second] = Const(regulator_error0)
    control.block.init_eqs[vr_command] = Const(field_voltage0 / supply_initial)
    field_supply: Var = control.algebraic(
        'AvailableFieldSupply',
        sym.min(
            vbmax,
            source_magnitude * _esst3a_fex(
                sym.safe_divide(kc * field_current, source_magnitude, Const(1.0)),
            ),
        ),
        Const(supply_initial),
    )
    regulator_limited: Expr = sym.hard_sat(vr_command, vrmin, vrmax)
    bridge_command: Var = control.lag(
        'RegulatorBridgeOutput', regulator_limited, bridge_time, selected.t1,
        Const(field_voltage0 / supply_initial), vrmin, vrmax,
    )
    field_voltage: Var = control.algebraic(
        'EFD', field_supply * bridge_command, Const(field_voltage0),
    )
    return control.finish((field_voltage,), 'IEEE ST10C parallel-path static excitation system')
