# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Native Q-control path of the REPCA1/REPCTA1 plant controller."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Repca1ReactiveMode(Enum):
    """Select the source RefFlag reactive-power or voltage-control path."""

    Q_CONTROL = 0
    VOLTAGE_CONTROL = 1


class Repca1VoltageCompensation(Enum):
    """Select reactive droop or source line-drop voltage compensation."""

    REACTIVE_DROOP = 0
    LINE_DROP = 1


class Repca1ReactivePlantSettings:
    """Store the source Q/V filter, PI, deadband and lead-lag fields."""

    __slots__ = ('tfltr', 'kp', 'ki', 'tft', 'tfv', 'vfrz',
                 'emax', 'emin', 'dbd1', 'dbd2', 'qmax', 'qmin', 'kc', 'rc', 'xc',
                 'mode', 'compensation')

    def __init__(self, tfltr: float = .02, kp: float = 1., ki: float = 1.,
                 tft: float = 0., tfv: float = .02, vfrz: float = .5,
                 emax: float = 1., emin: float = -1.,
                 dbd1: float = 0., dbd2: float = 0.,
                 qmax: float = 1.2, qmin: float = -1.2,
                 kc: float = 0., rc: float = 0., xc: float = 0.,
                 mode: Repca1ReactiveMode = Repca1ReactiveMode.Q_CONTROL,
                 compensation: Repca1VoltageCompensation = Repca1VoltageCompensation.REACTIVE_DROOP) -> None:
        """Store the 35.2 reactive-control gains, times and selectors.

        :param tfltr: Measured-Q filter time, seconds.
        :param kp: Q PI proportional gain.
        :param ki: Q PI integral gain.
        :param tft: Output lead time, seconds.
        :param tfv: Output lag time, seconds.
        :param vfrz: Voltage threshold freezing the PI integral.
        :param emax: Upper deadband-output limit.
        :param emin: Lower deadband-output limit.
        :param dbd1: Lower Q-error deadband threshold.
        :param dbd2: Upper Q-error deadband threshold.
        :param qmax: Maximum reactive plant order.
        :param qmin: Minimum reactive plant order.
        :param kc: VCFLAG=0 reactive droop contribution to voltage.
        :param rc: VCFLAG=1 line-drop resistance on the measurement base.
        :param xc: VCFLAG=1 line-drop reactance on the measurement base.
        :param mode: Q or compensated-voltage RefFlag path.
        :param compensation: Reactive droop or line-drop VCFlag path.
        :return: None.
        """
        self.tfltr: float = tfltr
        self.kp: float = kp
        self.ki: float = ki
        self.tft: float = tft
        self.tfv: float = tfv
        self.vfrz: float = vfrz
        self.emax: float = emax
        self.emin: float = emin
        self.dbd1: float = dbd1
        self.dbd2: float = dbd2
        self.qmax: float = qmax
        self.qmin: float = qmin
        self.kc: float = kc
        self.rc: float = rc
        self.xc: float = xc
        self.mode: Repca1ReactiveMode = mode
        self.compensation: Repca1VoltageCompensation = compensation


def repca1_line_drop_voltage(voltage: Expr, power: Expr, reactive_power: Expr,
                             rc: Expr, xc: Expr) -> Expr:
    """Evaluate ``|Vreg-(Rc+jXc)Ibranch|`` from local P/Q and voltage.

    The current is ``conj((P+jQ)/V)`` on the same measurement power base.

    :param voltage: Positive monitored voltage magnitude in per unit.
    :param power: Measured active power in per unit.
    :param reactive_power: Measured reactive power in per unit.
    :param rc: Line-drop resistance in per unit.
    :param xc: Line-drop reactance in per unit.
    :return: Compensated voltage magnitude in per unit.
    """
    denominator: Expr = sym.max(voltage, Const(.01))
    real_part: Expr = voltage - (rc * power + xc * reactive_power) / denominator
    imaginary_part: Expr = (xc * power - rc * reactive_power) / denominator
    return sym.sqrt(real_part * real_part + imaginary_part * imaginary_part)


def build_repca1_reactive_plant_template(
        vf: VarFactory, name: str = 'REPCA1 reactive plant',
        settings: Repca1ReactivePlantSettings | None = None,
) -> RmsModelTemplate:
    """Build source Q control or local compensated-voltage control.

    The caller supplies measured plant Q, its Q reference and monitored-bus
    voltage and local active power. External branch/bus measurements need
    separate host wiring.

    :param vf: Shared symbolic variable factory.
    :param name: Unique plant controller name.
    :param settings: Source Q-control fields.
    :return: Native reactive-power order for REECA1 Qext.
    :raises ValueError: Invalid times, gains, deadband or limits.
    """
    selected: Repca1ReactivePlantSettings = Repca1ReactivePlantSettings() if settings is None else settings
    values: tuple[float, ...] = (selected.tfltr, selected.kp, selected.ki,
                                 selected.tft, selected.tfv, selected.vfrz,
                                 selected.emax, selected.emin, selected.dbd1,
                                 selected.dbd2, selected.qmax, selected.qmin,
                                 selected.kc, selected.rc, selected.xc)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('REPCA1 reactive-plant parameters must be finite')
    elif min(selected.tfltr, selected.kp, selected.ki, selected.tft, selected.tfv) < 0:
        raise ValueError('REPCA1 Q-control gains and times must be nonnegative')
    elif selected.tfv == 0 and selected.tft > 0:
        raise ValueError('REPCA1 output lead requires a positive lag time')
    elif not selected.dbd1 <= 0 <= selected.dbd2:
        raise ValueError('REPCA1 Q deadband must contain zero')
    elif not selected.emin < 0 < selected.emax or not selected.qmin < selected.qmax:
        raise ValueError('REPCA1 Q-control limits are invalid')
    elif selected.kc < 0 or not isinstance(selected.mode, Repca1ReactiveMode):
        raise ValueError('REPCA1 voltage compensation mode or gain is invalid')
    elif not isinstance(selected.compensation, Repca1VoltageCompensation):
        raise ValueError('REPCA1 VCFLAG selection is invalid')
    else:
        pass

    control: ControlRealization = ControlRealization(vf, name)
    measured_q: Var = control.input('MeasuredPlantReactivePowerPu', Const(0.))
    q_reference: Var = control.input('PlantReactiveOrderPu', measured_q)
    monitored_voltage: Var = control.input('MonitoredVoltagePu', Const(1.))
    voltage_reference: Var = control.input('PlantVoltageOrderPu', monitored_voltage)
    measured_p: Var = control.input('MeasuredPlantPowerPu', Const(0.))
    tfltr: Var = control.parameter('TFLTR', selected.tfltr)
    kp: Var = control.parameter('KP', selected.kp)
    ki: Var = control.parameter('KI', selected.ki)
    tft: Var = control.parameter('TFT', selected.tft)
    tfv: Var = control.parameter('TFV', selected.tfv)
    vfrz: Var = control.parameter('VFRZ', selected.vfrz)
    emax: Var = control.parameter('EMAX', selected.emax)
    emin: Var = control.parameter('EMIN', selected.emin)
    dbd1: Var = control.parameter('DBD1', selected.dbd1)
    dbd2: Var = control.parameter('DBD2', selected.dbd2)
    qmax: Var = control.parameter('QMAX', selected.qmax)
    qmin: Var = control.parameter('QMIN', selected.qmin)
    filtered_q: Var = control.lag('FilteredPlantReactivePowerPu', measured_q,
                                  tfltr, selected.tfltr, measured_q)
    raw_error: Expr
    if selected.mode is Repca1ReactiveMode.VOLTAGE_CONTROL:
        compensated_voltage: Expr
        if selected.compensation is Repca1VoltageCompensation.LINE_DROP:
            rc: Var = control.parameter('RC', selected.rc)
            xc: Var = control.parameter('XC', selected.xc)
            compensated_voltage = repca1_line_drop_voltage(
                monitored_voltage, measured_p, measured_q, rc, xc,
            )
        else:
            kc: Var = control.parameter('KC', selected.kc)
            compensated_voltage = monitored_voltage + kc * measured_q
        filtered_voltage: Var = control.lag('FilteredPlantVoltagePu', compensated_voltage,
                                            tfltr, selected.tfltr, compensated_voltage)
        raw_error = voltage_reference - filtered_voltage
    else:
        raw_error = q_reference - filtered_q
    deadband_error: Expr = (sym.min(raw_error - dbd1, Const(0.))
                            + sym.max(raw_error - dbd2, Const(0.)))
    error: Expr = sym.hard_sat(deadband_error, emin, emax)
    pi_memory: Var = vf.add_var('PlantReactiveIntegral_' + name)
    q_command: Var = control.algebraic(
        'PlantReactiveCommandPu', sym.hard_sat(kp * error + pi_memory, qmin, qmax),
        measured_q,
    )
    # Freeze state s2 below Vfrz while retaining its initialized Q command.
    hold: Expr = Const(1.) - sym.heaviside(vfrz - monitored_voltage)
    control.differential(pi_memory, hold * ki * error, measured_q, qmin, qmax)
    qext: Var = control.lead_lag('PlantQextPu', q_command, tft, tfv,
                                  selected.tft, selected.tfv, measured_q)
    return control.finish((qext,), 'REPCA1 Q or local compensated-voltage plant control')
