# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""DERA1 voltage support and reactive current order from PSS/E 35.2 §17.1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Dera1ReactiveCurrentSettings:
    """Store the source voltage-control and reactive-current parameters."""

    __slots__ = ('pf_control', 'dbd1', 'dbd2', 'kqv', 'vref0', 'tiq',
                 'iqhl', 'iqll', 'initial_voltage', 'initial_active_power',
                 'initial_reactive_power', 'pf_angle')

    def __init__(
            self,
            pf_control: bool = False,
            dbd1: float = 0.0,
            dbd2: float = 0.0,
            kqv: float = 0.0,
            vref0: float = 0.0,
            tiq: float = 0.02,
            iqhl: float = 1.0,
            iqll: float = -1.0,
            initial_voltage: float = 1.0,
            initial_active_power: float = 0.0,
            initial_reactive_power: float = 0.0,
            pf_angle: float = 0.0,
    ) -> None:
        """Store source parameters and the solved point used for initialization.

        :param pf_control: True selects constant power-factor mode.
        :param dbd1: Lower voltage-error deadband edge, nonpositive pu.
        :param dbd2: Upper voltage-error deadband edge, nonnegative pu.
        :param kqv: Proportional voltage-control gain.
        :param vref0: Voltage reference; nonpositive selects the solved voltage.
        :param tiq: Reactive-current command lag time in seconds.
        :param iqhl: Upper limit on voltage-support reactive current.
        :param iqll: Lower limit on voltage-support reactive current.
        :param initial_voltage: Solved terminal-voltage magnitude in pu.
        :param initial_active_power: Solved active generation in pu.
        :param initial_reactive_power: Solved reactive generation in pu.
        :param pf_angle: Power-factor angle initialized from solved P/Q in radians.
        :return: None.
        """
        self.pf_control: bool = pf_control
        self.dbd1: float = dbd1
        self.dbd2: float = dbd2
        self.kqv: float = kqv
        self.vref0: float = vref0
        self.tiq: float = tiq
        self.iqhl: float = iqhl
        self.iqll: float = iqll
        self.initial_voltage: float = initial_voltage
        self.initial_active_power: float = initial_active_power
        self.initial_reactive_power: float = initial_reactive_power
        self.pf_angle: float = pf_angle


def build_dera1_reactive_current_template(
        vf: VarFactory,
        name: str = 'DERA1 reactive current',
        settings: Dera1ReactiveCurrentSettings | None = None,
) -> RmsModelTemplate:
    """Build DERA1's constant-Q/PF and voltage-support current path.

    :param vf: Shared symbolic variable factory.
    :param name: Unique model-component name.
    :param settings: DERA1 source values and solved initialization point.
    :return: Controller with open voltage, Pord, and Qref inputs.
    :raises ValueError: Invalid source settings or initialization point.
    """
    selected: Dera1ReactiveCurrentSettings = (
        Dera1ReactiveCurrentSettings() if settings is None else settings
    )
    values: tuple[float, ...] = (
        selected.dbd1, selected.dbd2, selected.kqv, selected.vref0,
        selected.tiq, selected.iqhl, selected.iqll, selected.initial_voltage,
        selected.initial_active_power, selected.initial_reactive_power,
        selected.pf_angle,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('DERA1 reactive-current settings must be finite')
    elif not isinstance(selected.pf_control, bool):
        raise ValueError('DERA1 PfFlag must be Boolean')
    elif selected.dbd1 > 0.0 or selected.dbd2 < 0.0 or selected.dbd1 > selected.dbd2:
        raise ValueError('DERA1 voltage deadband edges must straddle zero')
    elif selected.kqv < 0.0 or selected.tiq < 0.0:
        raise ValueError('DERA1 voltage gain and Tiq must be nonnegative')
    elif selected.iqll > selected.iqhl or selected.initial_voltage <= 0.0:
        raise ValueError('DERA1 reactive-current limits or voltage are invalid')
    elif selected.dbd1 == 0.0 and selected.dbd2 == 0.0 and selected.kqv > 0.0:
        raise ValueError('DERA1 voltage support requires a nonzero deadband')
    else:
        pass

    # PSS/E initializes a missing or out-of-deadband reference to terminal
    # voltage so voltage support contributes zero at the solved operating point.
    voltage_reference: float = selected.vref0
    initial_voltage_error: float = voltage_reference - selected.initial_voltage
    if selected.kqv > 0.0 and (
            voltage_reference <= 0.0
            or initial_voltage_error < selected.dbd1
            or initial_voltage_error > selected.dbd2):
        voltage_reference = selected.initial_voltage
    else:
        pass

    initial_q_reference: float = (
        selected.initial_active_power * math.tan(selected.pf_angle)
        if selected.pf_control else selected.initial_reactive_power
    )
    reference: float = initial_voltage_error
    initial_voltage_support: float = 0.0
    if voltage_reference - selected.initial_voltage < selected.dbd1:
        reference = voltage_reference - selected.initial_voltage - selected.dbd1
        initial_voltage_support = selected.kqv * reference
    elif voltage_reference - selected.initial_voltage > selected.dbd2:
        reference = voltage_reference - selected.initial_voltage - selected.dbd2
        initial_voltage_support = selected.kqv * reference
    else:
        pass
    initial_voltage_support = min(max(initial_voltage_support, selected.iqll), selected.iqhl)
    initial_current_order: float = (
        initial_q_reference / max(selected.initial_voltage, 0.01)
        + initial_voltage_support
    )

    control: ControlRealization = ControlRealization(vf, name)
    voltage: Var = control.input('FilteredTerminalVoltagePu', Const(selected.initial_voltage))
    active_order: Var = control.input('ActivePowerOrderPu', Const(selected.initial_active_power))
    reactive_reference: Var = control.input('ReactivePowerReferencePu', Const(initial_q_reference))
    reference_parameter: Var = control.parameter('VREF0', voltage_reference)
    lower_deadband: Var = control.parameter('DBD1', selected.dbd1)
    upper_deadband: Var = control.parameter('DBD2', selected.dbd2)
    gain: Var = control.parameter('KQV', selected.kqv)
    current_high: Var = control.parameter('IQHL', selected.iqhl)
    current_low: Var = control.parameter('IQLL', selected.iqll)
    q_reference: Expr = (
        active_order * Const(math.tan(selected.pf_angle))
        if selected.pf_control else reactive_reference
    )
    voltage_error: Expr = reference_parameter - voltage
    outside_deadband: Expr = (
        (voltage_error - lower_deadband) * sym.heaviside(lower_deadband - voltage_error)
        + (voltage_error - upper_deadband) * sym.heaviside(voltage_error - upper_deadband)
    )
    voltage_injection: Var = control.algebraic(
        'VoltageSupportReactiveCurrentPu',
        sym.hard_sat(gain * outside_deadband, current_low, current_high),
        Const(initial_voltage_support),
    )
    voltage_floor: Expr = sym.max(voltage, Const(0.01))
    unconstrained_q_current: Expr = q_reference / voltage_floor
    q_current_base: Var = control.lag(
        'ReactivePowerCurrentPu', unconstrained_q_current,
        control.parameter('TIQ', selected.tiq), selected.tiq,
        Const(initial_q_reference / max(selected.initial_voltage, 0.01)),
    )
    reactive_current: Var = control.algebraic(
        'ReactiveCurrentCommandPu', q_current_base + voltage_injection,
        Const(initial_current_order),
    )
    return control.finish(
        (reactive_current, voltage_injection),
        'DERA1 constant-Q/PF and proportional voltage-support current path',
    )
