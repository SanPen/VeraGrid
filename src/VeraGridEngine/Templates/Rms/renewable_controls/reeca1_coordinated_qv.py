# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""REECA1 coordinated Q/V control for PFFLAG=0, VFLAG=1, QFLAG=1."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Reeca1CoordinatedQvSettings:
    """Store cascaded reactive-power and voltage PI gains and output bounds."""

    __slots__ = ('qmin', 'qmax', 'vmin', 'vmax', 'kqp', 'kqi', 'kvp', 'kvi', 'tiq')

    def __init__(self, qmin: float = -1., qmax: float = 1.,
                 vmin: float = .8, vmax: float = 1.2,
                 kqp: float = 1., kqi: float = 1.,
                 kvp: float = 1., kvi: float = 1., tiq: float = .02) -> None:
        """Store source regulator parameters on the generator MVA base.

        :param qmin: Lower reactive-power reference bound.
        :param qmax: Upper reactive-power reference bound.
        :param vmin: Lower Q-regulator voltage-reference bound.
        :param vmax: Upper Q-regulator voltage-reference bound.
        :param kqp: Reactive-power proportional gain.
        :param kqi: Reactive-power integral gain.
        :param kvp: Voltage proportional gain.
        :param kvi: Voltage integral gain.
        :param tiq: Source reactive-current command lag time in seconds.
        :return: None.
        """
        self.qmin: float = qmin
        self.qmax: float = qmax
        self.vmin: float = vmin
        self.vmax: float = vmax
        self.kqp: float = kqp
        self.kqi: float = kqi
        self.kvp: float = kvp
        self.kvi: float = kvi
        self.tiq: float = tiq


def add_reeca1_voltage_pi(
        control: ControlRealization, voltage_reference: Expr,
        filtered_voltage: Expr, fault_flag: Expr, iq_capability: Expr,
        kvp: Expr, kvi: Expr, initial_current: Expr,
) -> Var:
    """Add the shared fault-frozen voltage PI with moving current stops.

    :param control: Owning controller realization.
    :param voltage_reference: Voltage target after the selected VFLAG branch.
    :param filtered_voltage: Measured terminal voltage in per unit.
    :param fault_flag: One while the source voltage-dip state is active.
    :param iq_capability: Live positive reactive-current magnitude limit.
    :param kvp: Voltage proportional gain.
    :param kvi: Voltage integral gain.
    :param initial_current: Equilibrium reactive current for both output and memory.
    :return: Bounded reactive-current command.
    """
    # The proportional output remains live while the integral memory freezes
    # during faults. Moving state stops prevent hidden windup at the Iq limit.
    voltage_error: Expr = voltage_reference - filtered_voltage
    v_integral: Var = control.vf.add_var('VoltageRegulatorIntegral_' + control.name)
    iq_command: Var = control.algebraic(
        'RegulatedReactiveCurrentPu',
        sym.hard_sat(kvp * voltage_error + v_integral,
                     -iq_capability, iq_capability), initial_current,
    )
    control.differential(v_integral,
                         (Const(1.) - fault_flag) * kvi * voltage_error,
                         initial_current,
                         -iq_capability - kvp * voltage_error,
                         iq_capability - kvp * voltage_error)
    return iq_command


def build_reeca1_coordinated_qv_template(
        vf: VarFactory,
        name: str = 'REECA1 coordinated Q V',
        settings: Reeca1CoordinatedQvSettings | None = None,
) -> RmsModelTemplate:
    """Build source Q PI then voltage PI, with capability and fault feedback.

    The Q regulator creates a bounded voltage reference; the voltage
    regulator produces an Iq command bounded by the live current capability.
    Both integrator memories freeze during source voltage-dip states, then the
    source TIQ lag produces the externally connected current command.

    :param vf: Shared symbolic variable factory.
    :param name: Unique controller instance name.
    :param settings: Q/V gains, reference bounds and TIQ lag.
    :return: Controller with Q reference/measurement, voltage, fault and capability inputs.
    :raises ValueError: Nonfinite, unordered or negative-gain settings.
    """
    selected: Reeca1CoordinatedQvSettings = Reeca1CoordinatedQvSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.qmin, selected.qmax, selected.vmin,
                                 selected.vmax, selected.kqp, selected.kqi,
                                 selected.kvp, selected.kvi, selected.tiq)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('REECA1 Q/V settings must be finite')
    elif selected.qmax <= selected.qmin or selected.vmin <= 0 or selected.vmax <= selected.vmin:
        raise ValueError('REECA1 Q/V bounds are invalid')
    elif min(selected.kqp, selected.kqi, selected.kvp, selected.kvi) < 0:
        raise ValueError('REECA1 Q/V gains must be nonnegative')
    elif selected.tiq < 0:
        raise ValueError('REECA1 Q/V Tiq must be nonnegative')
    else:
        pass
    control: ControlRealization = ControlRealization(vf, name)
    q_reference: Var = control.input('QReferencePu', Const(0.))
    q_generated: Var = control.input('MeasuredReactivePowerPu', Const(0.))
    filtered_voltage: Var = control.input('FilteredVoltagePu', Const(1.))
    fault_flag: Var = control.input('VoltageDipFlag', Const(0.))
    iq_capability: Var = control.input('ReactiveCapabilityPu', Const(1.))
    qmin: Var = control.parameter('QMIN', selected.qmin)
    qmax: Var = control.parameter('QMAX', selected.qmax)
    vmin: Var = control.parameter('VMIN', selected.vmin)
    vmax: Var = control.parameter('VMAX', selected.vmax)
    kqp: Var = control.parameter('KQP', selected.kqp)
    kqi: Var = control.parameter('KQI', selected.kqi)
    kvp: Var = control.parameter('KVP', selected.kvp)
    kvi: Var = control.parameter('KVI', selected.kvi)
    enabled: Expr = Const(1.) - fault_flag

    # Q reference clipping occurs before subtracting generated Q. Moving
    # integrator stops preserve the PI output bounds under proportional action.
    q_error: Expr = sym.hard_sat(q_reference, qmin, qmax) - q_generated
    q_integral: Var = vf.add_var('QRegulatorIntegral_' + name)
    voltage_reference: Var = control.algebraic(
        'QRegulatorVoltageReferencePu',
        sym.hard_sat(kqp * q_error + q_integral, vmin, vmax), Const(1.),
    )
    control.differential(q_integral, enabled * kqi * q_error, Const(1.),
                         vmin - kqp * q_error, vmax - kqp * q_error)

    iq_regulator: Var = add_reeca1_voltage_pi(
        control, voltage_reference, filtered_voltage, fault_flag,
        iq_capability, kvp, kvi, Const(0.),
    )
    tiq: Var = control.parameter('TIQ', selected.tiq)
    iq_command: Var = control.lag('ReactiveCurrentCommandPu', iq_regulator, tiq,
                                  selected.tiq, Const(0.))
    return control.finish((iq_command,), 'REECA1 coordinated Q/V PI regulators')
