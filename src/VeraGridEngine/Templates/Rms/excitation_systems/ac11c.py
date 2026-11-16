# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Continuous control stages used by the IEEE AC11C excitation model."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import _quadratic_saturation_coefficients
from VeraGridEngine.enumerations import DeviceType


class Ac11cLimiterLocation(Enum):
    """Select the documented summation, alternate-controller or output gate."""

    ERROR_SUM = 1
    ALTERNATE = 2
    REGULATOR_OUTPUT = 3


class Ac11cPowerSource(Enum):
    """Select terminal-fed or independent controlled-rectifier power."""

    TERMINAL = 1
    INDEPENDENT = 2


class Ac11cPssLocation(Enum):
    """Select the AC11C stabilizer connection point."""

    UNUSED = 0
    ERROR_SUM = 1
    SWLIM = 2
    STABILIZER_PI = 3


class Ac11cParameters:
    """PSS/E AC11C regulator, exciter and dual-source coefficients."""

    __slots__ = (
        'tr', 'kpa', 'tia', 'kpu', 'tiu', 'kb', 'tb', 'kpo', 'tio',
        'vrsmx', 'vrsmn', 'vrmax', 'vrmin', 'vamax', 'vamin', 'te',
        'kc', 'kd', 'ke', 'vfemax', 'vemin', 'e1', 'se1', 'e2', 'se2',
        'kp', 'ki1', 'xl', 'theta_p', 'kc1', 'vb1max', 'ki2', 'kc2',
        'vb2max', 'kboost', 'vboost', 'pss_location', 'oel_location',
        'uel_location', 'scl_location', 'power_source', 'efd0', 'ifd0',
        'vt0', 'it0',
    )

    def __init__(
            self,
            tr: float = 0.01,
            kpa: float = 20.0,
            tia: float = 1.0,
            kpu: float = 20.0,
            tiu: float = 1.0,
            kb: float = 0.1,
            tb: float = 0.1,
            kpo: float = 20.0,
            tio: float = 1.0,
            vrsmx: float = 3.0,
            vrsmn: float = -3.0,
            vrmax: float = 5.0,
            vrmin: float = -5.0,
            vamax: float = 5.0,
            vamin: float = -5.0,
            te: float = 0.5,
            kc: float = 0.1,
            kd: float = 0.1,
            ke: float = 1.0,
            vfemax: float = 5.0,
            vemin: float = 0.0,
            e1: float = 3.0,
            se1: float = 0.1,
            e2: float = 4.0,
            se2: float = 0.3,
            kp: float = 1.0,
            ki1: float = 0.0,
            xl: float = 0.0,
            theta_p: float = 0.0,
            kc1: float = 0.1,
            vb1max: float = 5.0,
            ki2: float = 0.0,
            kc2: float = 0.0,
            vb2max: float = 5.0,
            kboost: float = 0.0,
            vboost: float = 2.0,
            pss_location: Ac11cPssLocation = Ac11cPssLocation.UNUSED,
            oel_location: Ac11cLimiterLocation = Ac11cLimiterLocation.ERROR_SUM,
            uel_location: Ac11cLimiterLocation = Ac11cLimiterLocation.ERROR_SUM,
            scl_location: Ac11cLimiterLocation = Ac11cLimiterLocation.ERROR_SUM,
            power_source: Ac11cPowerSource = Ac11cPowerSource.TERMINAL,
            efd0: float = 1.0,
            ifd0: float = 1.0,
            vt0: float = 1.0,
            it0: float = 0.0,
    ) -> None:
        """Store release fields and topology selectors in source units.

        :param tr: Voltage transducer time constant in seconds.
        :param kpa: AVR proportional gain.
        :param tia: AVR integral time in seconds.
        :param kpu: UEL proportional gain.
        :param tiu: UEL integral time in seconds.
        :param kb: Shared derivative-filter gain.
        :param tb: Shared derivative-filter time in seconds.
        :param kpo: OEL proportional gain.
        :param tio: OEL integral time in seconds.
        :param vrsmx: PSS regulator upper limit.
        :param vrsmn: PSS regulator lower limit.
        :param vrmax: Regulator upper limit.
        :param vrmin: Regulator lower limit.
        :param vamax: Exciter-control upper limit.
        :param vamin: Exciter-control lower limit.
        :param te: Exciter time constant in seconds.
        :param kc: Output rectifier loading factor.
        :param kd: Exciter demagnetization factor.
        :param ke: Exciter field gain.
        :param vfemax: Exciter field-current ceiling.
        :param vemin: Exciter internal-voltage floor.
        :param e1: First saturation sample voltage.
        :param se1: Saturation factor at e1.
        :param e2: Second saturation sample voltage.
        :param se2: Saturation factor at e2.
        :param kp: Terminal potential-source voltage gain.
        :param ki1: Terminal potential-source current gain.
        :param xl: Terminal potential-source reactance.
        :param theta_p: Terminal potential-source phase in degrees.
        :param kc1: First source rectifier loading factor.
        :param vb1max: First source field-voltage ceiling.
        :param ki2: Additive source terminal-current gain.
        :param kc2: Additive source rectifier loading factor.
        :param vb2max: Additive source field-voltage ceiling.
        :param kboost: Additive source gain.
        :param vboost: Terminal-voltage threshold for releasing boost.
        :param pss_location: Stabilizer input position.
        :param oel_location: OEL input position.
        :param uel_location: UEL input position.
        :param scl_location: SCL input position.
        :param power_source: Controlled rectifier source selection.
        :param efd0: Initial generator field voltage.
        :param ifd0: Initial generator field current.
        :param vt0: Initial terminal-voltage magnitude.
        :param it0: Initial terminal-current magnitude.
        """
        self.tr: float = tr
        self.kpa: float = kpa
        self.tia: float = tia
        self.kpu: float = kpu
        self.tiu: float = tiu
        self.kb: float = kb
        self.tb: float = tb
        self.kpo: float = kpo
        self.tio: float = tio
        self.vrsmx: float = vrsmx
        self.vrsmn: float = vrsmn
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.te: float = te
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.vfemax: float = vfemax
        self.vemin: float = vemin
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.kp: float = kp
        self.ki1: float = ki1
        self.xl: float = xl
        self.theta_p: float = theta_p
        self.kc1: float = kc1
        self.vb1max: float = vb1max
        self.ki2: float = ki2
        self.kc2: float = kc2
        self.vb2max: float = vb2max
        self.kboost: float = kboost
        self.vboost: float = vboost
        self.pss_location: Ac11cPssLocation = pss_location
        self.oel_location: Ac11cLimiterLocation = oel_location
        self.uel_location: Ac11cLimiterLocation = uel_location
        self.scl_location: Ac11cLimiterLocation = scl_location
        self.power_source: Ac11cPowerSource = power_source
        self.efd0: float = efd0
        self.ifd0: float = ifd0
        self.vt0: float = vt0
        self.it0: float = it0


def _ac11c_initial_internal_voltage(field: float, loading: float) -> float:
    """Invert the standard rectifier curve for a numeric initial field point.

    :param field: Delivered generator field voltage.
    :param loading: Rectifier commutation loading.
    :return: Initial internal exciter voltage.
    """
    if loading <= 0.0:
        return field
    else:
        pass
    first: float = field + 0.577 * loading
    middle: float = math.sqrt((field * field + loading * loading) / 0.75)
    last: float = field / 1.732 + loading
    if first - loading / 0.433 > 0.0:
        return first
    elif middle - loading / 0.75 > 0.0:
        return middle
    else:
        return last


def _ac11c_fex_value(normalized_current: float) -> float:
    """Evaluate the IEEE brushless rectifier function at initialization.

    :param normalized_current: Normalized rectifier current.
    :return: Rectifier voltage factor.
    """
    if normalized_current < 0.0:
        return 1.0
    elif normalized_current < 0.433:
        return 1.0 - 0.577 * normalized_current
    elif normalized_current < 0.75:
        return math.sqrt(0.75 - normalized_current * normalized_current)
    elif normalized_current < 1.0:
        return 1.732 * (1.0 - normalized_current)
    else:
        return 0.0


def build_ac11c_template(
        vf: VarFactory,
        name: str | None = None,
        parameters: Ac11cParameters | None = None,
) -> RmsModelTemplate:
    """Build the nine-state AC11C regulator, dual sources and rotating exciter.

    The exposed ports are reference voltage, stabilizer voltage, OEL/UEL/SCL
    signals, rectangular terminal voltage/current and generator field current.
    OEL/UEL can be summed, select their alternate controller, or take over at
    the regulator output. PSS uses its error-sum, SWLIM or filtered-PI path.
    The PSS/E note marks the SCL takeover signals unused; non-summation SCL
    selections therefore remain inactive, matching that release behavior.

    :param vf: Shared symbolic factory for the composed machine model.
    :param name: Optional instance label.
    :param parameters: PSS/E coefficients, selector positions and initial point.
    :return: Native AC11C model with field voltage as its first output.
    :raises ValueError: Invalid parameter domains or infeasible initial supply.
    """
    p: Ac11cParameters = Ac11cParameters() if parameters is None else parameters
    values: tuple[float, ...] = (
        p.tr, p.kpa, p.tia, p.kpu, p.tiu, p.kb, p.tb, p.kpo, p.tio,
        p.vrsmx, p.vrsmn, p.vrmax, p.vrmin, p.vamax, p.vamin, p.te,
        p.kc, p.kd, p.ke, p.vfemax, p.vemin, p.e1, p.se1, p.e2, p.se2,
        p.kp, p.ki1, p.xl, p.theta_p, p.kc1, p.vb1max, p.ki2, p.kc2,
        p.vb2max, p.kboost, p.vboost, p.efd0, p.ifd0, p.vt0, p.it0,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC11C coefficients must be finite')
    elif min(p.tr, p.kb, p.tb, p.kc, p.kd, p.kc1, p.kc2, p.ki1, p.ki2,
             p.xl, p.kboost, p.vemin, p.e1, p.se1, p.e2, p.se2) < 0.0:
        raise ValueError('AC11C times and source/field coefficients must be nonnegative')
    elif min(p.kpa, p.tia, p.kpu, p.tiu, p.kpo, p.tio, p.te, p.ke,
             p.vfemax, p.kp) <= 0.0:
        raise ValueError('AC11C regulator and exciter gains/times must be positive')
    elif (p.vrmax <= p.vrmin or p.vamax <= p.vamin or p.vrsmx <= p.vrsmn
          or p.vb1max < 0.0 or p.vb2max < 0.0 or p.vemin < 0.0):
        raise ValueError('AC11C voltage limits must be ordered and nonnegative where required')
    elif (p.se1 == 0.0) != (p.se2 == 0.0):
        raise ValueError('AC11C magnetic saturation needs two samples or two zeros')
    elif p.se1 > 0.0 and (p.e1 == p.e2 or (p.e2 - p.e1) * (p.e2 * p.se2 - p.e1 * p.se1) <= 0.0):
        raise ValueError('AC11C saturation samples must define a monotone curve')
    elif (not isinstance(p.pss_location, Ac11cPssLocation)
          or not isinstance(p.oel_location, Ac11cLimiterLocation)
          or not isinstance(p.uel_location, Ac11cLimiterLocation)
          or not isinstance(p.scl_location, Ac11cLimiterLocation)
          or not isinstance(p.power_source, Ac11cPowerSource)):
        raise ValueError('AC11C selector type is invalid')
    elif p.efd0 <= 0.0 or p.ifd0 < 0.0 or p.vt0 <= 0.0 or p.it0 < 0.0:
        raise ValueError('AC11C initial operating point must be physically feasible')
    else:
        pass

    label: str = 'AC11C' if name is None else name
    control: ControlRealization = ControlRealization(vf, label)
    tr: Var = control.parameter('TR', p.tr)
    te: Var = control.parameter('TE', p.te)
    kc: Var = control.parameter('KC', p.kc)
    kd: Var = control.parameter('KD', p.kd)
    ke: Var = control.parameter('KE', p.ke)
    vfemax: Var = control.parameter('VFEMAX', p.vfemax)
    vemin: Var = control.parameter('VEMIN', p.vemin)
    e1: Var = control.parameter('E1', p.e1)
    se1: Var = control.parameter('SE1', p.se1)
    e2: Var = control.parameter('E2', p.e2)
    se2: Var = control.parameter('SE2', p.se2)
    kp: Var = control.parameter('KP', p.kp)
    ki1: Var = control.parameter('KI1', p.ki1)
    xl: Var = control.parameter('XL', p.xl)
    theta: Var = control.parameter('THETAP', p.theta_p)
    kc1: Var = control.parameter('KC1', p.kc1)
    vb1max: Var = control.parameter('VB1MAX', p.vb1max)
    ki2: Var = control.parameter('KI2', p.ki2)
    kc2: Var = control.parameter('KC2', p.kc2)
    vb2max: Var = control.parameter('VB2MAX', p.vb2max)
    kboost: Var = control.parameter('KBOOST', p.kboost)
    vboost: Var = control.parameter('VBOOST', p.vboost)
    field0: Var = control.parameter('Efd0Pu', p.efd0)
    current0: Var = control.parameter('Ifd0Pu', p.ifd0)
    voltage0: Var = control.parameter('Vt0Pu', p.vt0)

    reference: Var = control.input('VrefPu', voltage0)
    stabilizer: Var = control.input('VsPu', Const(0.0))
    overexcitation: Var = control.input('OelPu', Const(0.0))
    underexcitation: Var = control.input('UelPu', Const(0.0))
    stator_current_limiter: Var = control.input('SclSumPu', Const(0.0))
    voltage_real: Var = control.input('VtRealPu', voltage0)
    voltage_imag: Var = control.input('VtImagPu', Const(0.0))
    current_real: Var = control.input('ItRealPu', Const(p.it0))
    current_imag: Var = control.input('ItImagPu', Const(0.0))
    field_current: Var = control.input('IfdPu', current0)
    terminal_voltage: Expr = sym.sqrt(voltage_real * voltage_real + voltage_imag * voltage_imag)
    current_magnitude: Expr = sym.sqrt(current_real * current_real + current_imag * current_imag)
    internal0_value: float = _ac11c_initial_internal_voltage(p.efd0, p.kc * p.ifd0)
    internal0: Var = control.parameter('Ve0Pu', internal0_value)
    saturation_threshold: Expr
    saturation_coefficient: Expr
    if p.se1 == 0.0:
        saturation_coefficient: Expr = Const(0.0)
        saturation_threshold = Const(0.0)
        saturation_gain_value: float = 0.0
        saturation_start_value: float = 0.0
    else:
        saturation_threshold, saturation_coefficient = _quadratic_saturation_coefficients(
            e1, se1, e2, se2,
        )
        ratio_value: float = math.sqrt((p.se1 * p.e1) / (p.se2 * p.e2))
        saturation_start_value = p.e2 - (p.e1 - p.e2) / (ratio_value - 1.0)
        saturation_gain_value = (
            p.se2 * p.e2 * (ratio_value - 1.0) ** 2 / (p.e1 - p.e2) ** 2
        )
    saturation0_value: float = (
        saturation_gain_value * max(internal0_value - saturation_start_value, 0.0) ** 2
    )
    exciter_field_current0_value: float = (
        p.ke * internal0_value + saturation0_value + p.kd * p.ifd0
    )
    exciter_field_current0: Expr = (
        ke * internal0 + saturation_gain_value
        * sym.max(internal0 - Const(saturation_start_value), Const(0.0)) ** 2
        + kd * current0
    )
    angle: Expr = theta * Const(math.pi / 180.0)
    kp_real: Expr = kp * sym.cos(angle)
    kp_imag: Expr = kp * sym.sin(angle)
    compound_real: Expr = ki1 + kp_real * xl
    compound_imag: Expr = kp_imag * xl
    source1_real: Expr = (
        kp_real * voltage_real - kp_imag * voltage_imag
        - compound_real * current_imag - compound_imag * current_real
    )
    source1_imag: Expr = (
        kp_real * voltage_imag + kp_imag * voltage_real
        + compound_real * current_real - compound_imag * current_imag
    )
    terminal_source: Expr = sym.sqrt(
        source1_real * source1_real + source1_imag * source1_imag,
    )
    source1: Expr = terminal_source if p.power_source is Ac11cPowerSource.TERMINAL else kp
    source2: Expr = sym.max(kboost + ki2 * current_magnitude, Const(0.001))
    boost_active: Expr = sym.heaviside(vboost - terminal_voltage)
    phase_value: float = math.radians(p.theta_p)
    kp_real_value: float = p.kp * math.cos(phase_value)
    kp_imag_value: float = p.kp * math.sin(phase_value)
    compound_real_value: float = p.ki1 + kp_real_value * p.xl
    compound_imag_value: float = kp_imag_value * p.xl
    source_real_initial: float = (
        kp_real_value * p.vt0 - compound_imag_value * p.it0
    )
    source_imag_initial: float = (
        kp_imag_value * p.vt0 + compound_real_value * p.it0
    )
    source1_initial: float = (
        p.kp if p.power_source is Ac11cPowerSource.INDEPENDENT else
        math.hypot(source_real_initial, source_imag_initial)
    )
    source2_initial: float = max(p.kboost + p.ki2 * p.it0, 0.001)
    if source1_initial <= 0.0:
        raise ValueError('AC11C selected first source has zero initial voltage')
    else:
        pass
    initial_fex1: float = _ac11c_fex_value(
        p.kc1 * exciter_field_current0_value / source1_initial,
    )
    initial_fex2: float = _ac11c_fex_value(
        p.kc2 * exciter_field_current0_value / source2_initial,
    )
    source1_output0: float = min(p.vb1max, source1_initial * initial_fex1)
    source2_output0: float = (
        min(p.vb2max, source2_initial * initial_fex2) if p.vt0 <= p.vboost else 0.0
    )
    total_source0: float = source1_output0 + source2_output0
    if total_source0 <= 0.0:
        raise ValueError('AC11C initial power-source voltage must be positive')
    else:
        pass
    regulator_initial_value: float = exciter_field_current0_value / total_source0
    if not p.vamin <= regulator_initial_value <= p.vamax:
        raise ValueError('AC11C initial source demand exceeds exciter-control limits')
    else:
        pass
    normalized1_initial: Expr = sym.safe_divide(
        kc1 * exciter_field_current0, source1, Const(1.0),
    )
    normalized2_initial: Expr = sym.safe_divide(
        kc2 * exciter_field_current0, source2, Const(1.0),
    )
    source1_output_initial: Expr = sym.hard_sat(
        source1 * _esst3a_fex(normalized1_initial), Const(0.0), vb1max,
    )
    source2_output_initial: Expr = sym.hard_sat(
        source2 * _esst3a_fex(normalized2_initial), Const(0.0), vb2max,
    )
    total_source_initial: Expr = (
        source1_output_initial + boost_active * source2_output_initial
    )
    regulator_initial: Expr = sym.safe_divide(
        exciter_field_current0, total_source_initial, Const(regulator_initial_value),
    )

    measured: Var = control.lag(
        'MeasuredTerminalVoltagePu', terminal_voltage, tr, p.tr, voltage0,
    )
    error: Expr = reference - measured
    if p.pss_location is Ac11cPssLocation.ERROR_SUM:
        error += stabilizer
    else:
        pass
    if p.oel_location is Ac11cLimiterLocation.ERROR_SUM:
        error += overexcitation
    else:
        pass
    if p.uel_location is Ac11cLimiterLocation.ERROR_SUM:
        error += underexcitation
    else:
        pass
    if p.scl_location is Ac11cLimiterLocation.ERROR_SUM:
        error += stator_current_limiter
    else:
        pass
    avr: Var = add_ac11c_filtered_pi(
        control, 'Avr', error, Const(0.0), regulator_initial / Const(p.kpa),
        p.kpa, p.tia, p.kb, p.tb, p.vrmin, p.vrmax, regulator_initial,
    )
    uel: Var = add_ac11c_filtered_pi(
        control, 'Uel', error, Const(0.0), regulator_initial / Const(p.kpu),
        p.kpu, p.tiu, p.kb, p.tb, p.vrmin, p.vrmax, regulator_initial,
    )
    oel: Var = add_ac11c_pi(
        control, 'Oel', error, regulator_initial / Const(p.kpo),
        p.kpo, p.tio, p.vrmin, p.vrmax, regulator_initial,
    )
    active_uel: Expr = sym.heaviside(sym.abs(underexcitation) - Const(1.0e-6))
    active_oel: Expr = sym.heaviside(sym.abs(overexcitation) - Const(1.0e-6))
    pss_input: Expr = stabilizer
    if p.pss_location is Ac11cPssLocation.SWLIM:
        limiter_active: Expr = sym.max(active_uel, active_oel)
        pss_input = stabilizer * limiter_active
    else:
        pass
    pss: Var = add_ac11c_filtered_pi(
        control, 'Pss', pss_input, Const(0.0), Const(0.0),
        p.kpa, p.tia, p.kb, p.tb, p.vrsmn, p.vrsmx, Const(0.0),
    )
    control_output: Expr = avr
    if p.uel_location is Ac11cLimiterLocation.ALTERNATE:
        control_output = (Const(1.0) - active_uel) * control_output + active_uel * uel
    else:
        pass
    if p.oel_location is Ac11cLimiterLocation.ALTERNATE:
        control_output = (Const(1.0) - active_oel) * control_output + active_oel * oel
    else:
        pass
    if p.pss_location is Ac11cPssLocation.SWLIM:
        non_limited: Expr = Const(1.0) - limiter_active
        control_output += non_limited * stabilizer + pss
    elif p.pss_location is Ac11cPssLocation.STABILIZER_PI:
        control_output += pss
    else:
        pass
    if p.uel_location is Ac11cLimiterLocation.REGULATOR_OUTPUT:
        control_output = (
            (Const(1.0) - active_uel) * control_output
            + active_uel * sym.max(control_output, underexcitation)
        )
    else:
        pass
    if p.oel_location is Ac11cLimiterLocation.REGULATOR_OUTPUT:
        control_output = (
            (Const(1.0) - active_oel) * control_output
            + active_oel * sym.min(control_output, overexcitation)
        )
    else:
        pass
    exciter_control: Var = control.algebraic(
        'ExciterControlPu', sym.hard_sat(control_output, Const(p.vamin), Const(p.vamax)),
        regulator_initial,
    )
    internal: Var = vf.add_var(name='InternalExciterVoltagePu_' + label)
    dynamic_saturation: Expr = saturation_coefficient * sym.max(
        internal - saturation_threshold, Const(0.0),
    ) ** 2
    exciter_field_current: Var = control.algebraic(
        'ExciterFieldCurrentPu', ke * internal + dynamic_saturation + kd * field_current,
        exciter_field_current0,
    )
    field: Var = control.algebraic(
        'EfdPu', internal * _esst3a_fex(sym.safe_divide(kc * field_current, internal, Const(1.0))),
        field0,
    )
    if p.power_source is Ac11cPowerSource.TERMINAL:
        selected_source1: Expr = terminal_source
    else:
        selected_source1 = kp
    normalized1 = sym.safe_divide(kc1 * exciter_field_current, selected_source1, Const(1.0))
    normalized2 = sym.safe_divide(kc2 * exciter_field_current, source2, Const(1.0))
    source1_voltage = sym.hard_sat(
        selected_source1 * _esst3a_fex(normalized1), Const(0.0), vb1max,
    )
    source2_voltage = sym.hard_sat(
        source2 * _esst3a_fex(normalized2), Const(0.0), vb2max,
    )
    total_source = source1_voltage + boost_active * source2_voltage
    exciter_input: Expr = exciter_control * total_source
    upper_internal: Expr = sym.safe_divide(
        vfemax - dynamic_saturation - kd * field_current, ke, Const(p.efd0),
    )
    control.differential(
        internal, (exciter_input - exciter_field_current) / te,
        internal0, vemin, upper_internal,
    )
    return control.finish(
        (field,), 'Nine-state AC11C voltage regulation with dual rectifier sources and boost release',
    )


def add_ac11c_pi(
        control: ControlRealization,
        stage_name: str,
        error: Expr,
        integral_initial: Expr | Const,
        proportional_gain: float,
        integral_time: float,
        output_minimum: float,
        output_maximum: float,
        output_initial: Expr | Const,
) -> Var:
    """Add the source OEL PI branch with its regulator-output limits.

    :param control: Controller graph receiving the PI state and output.
    :param stage_name: Distinct identifier for this controller branch.
    :param error: Live voltage error entering the PI branch.
    :param integral_initial: Operating-point value of the PI memory.
    :param proportional_gain: Positive Kp coefficient.
    :param integral_time: Positive Ti coefficient in seconds.
    :param output_minimum: Lower regulator output limit.
    :param output_maximum: Upper regulator output limit.
    :param output_initial: Operating-point value of the limited output.
    :return: Limited proportional-integral output.
    :raises ValueError: Invalid gains, times or output limits.
    """
    values: tuple[float, ...] = (
        proportional_gain, integral_time, output_minimum, output_maximum,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC11C PI settings must be finite')
    elif proportional_gain <= 0.0 or integral_time <= 0.0:
        raise ValueError('AC11C PI gain and integral time must be positive')
    elif output_maximum <= output_minimum:
        raise ValueError('AC11C PI output limits must be ordered')
    else:
        pass

    gain: Var = control.parameter(stage_name + 'Kp', proportional_gain)
    ti: Var = control.parameter(stage_name + 'Ti', integral_time)
    integral: Var = control.vf.add_var(name=stage_name + 'Integral_' + control.name)
    control.differential(integral, error / ti, integral_initial)
    minimum: Var = control.parameter(stage_name + 'Minimum', output_minimum)
    maximum: Var = control.parameter(stage_name + 'Maximum', output_maximum)
    return control.algebraic(
        stage_name + 'Output', sym.hard_sat(gain * (error + integral), minimum, maximum),
        output_initial,
    )


def add_ac11c_filtered_pi(
        control: ControlRealization,
        stage_name: str,
        error: Expr,
        error_initial: Expr | Const,
        integral_initial: Expr | Const,
        proportional_gain: float,
        integral_time: float,
        filter_gain: float,
        filter_time: float,
        output_minimum: float,
        output_maximum: float,
        output_initial: Expr | Const,
) -> Var:
    """Add an AC11C PI controller followed by its filtered derivative stage.

    The source diagram implements ``(Kp + Kp/(s*Ti))`` followed by
    ``Kp/(Kp+s*Kb*Tb)``. The second factor is a first-order lag with time
    ``Kb*Tb/Kp``. A zero filter time reduces that stage algebraically.

    :param control: Controller graph receiving the stage states and equations.
    :param stage_name: Distinct name for this AVR, UEL or PSS branch.
    :param error: Live voltage error entering the PI branch.
    :param error_initial: Operating-point value of the branch error.
    :param integral_initial: Operating-point value of the PI memory.
    :param proportional_gain: Positive Kp coefficient.
    :param integral_time: Positive Ti coefficient in seconds.
    :param filter_gain: Nonnegative Kb coefficient.
    :param filter_time: Nonnegative Tb coefficient in seconds.
    :param output_minimum: Lower filtered output limit.
    :param output_maximum: Upper filtered output limit.
    :param output_initial: Equilibrium value of the stage output.
    :return: Saturated filtered PI output.
    :raises ValueError: Invalid gains, times or output limits.
    """
    values: tuple[float, ...] = (
        proportional_gain, integral_time, filter_gain, filter_time,
        output_minimum, output_maximum,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC11C filtered-PI settings must be finite')
    elif proportional_gain <= 0.0 or integral_time <= 0.0:
        raise ValueError('AC11C filtered-PI gain and integral time must be positive')
    elif filter_gain < 0.0 or filter_time < 0.0:
        raise ValueError('AC11C derivative filter settings must be nonnegative')
    elif output_maximum <= output_minimum:
        raise ValueError('AC11C filtered-PI output limits must be ordered')
    else:
        pass

    gain: Var = control.parameter(stage_name + 'Kp', proportional_gain)
    ti: Var = control.parameter(stage_name + 'Ti', integral_time)
    kb: Var = control.parameter(stage_name + 'Kb', filter_gain)
    tb: Var = control.parameter(stage_name + 'Tb', filter_time)
    integral: Var = control.vf.add_var(name=stage_name + 'Integral_' + control.name)
    control.differential(integral, error / ti, integral_initial)
    pi_output: Expr = gain * (error + integral)
    pi_initial: Expr = gain * (error_initial + integral_initial)
    filter_lag: Expr = kb * tb / gain
    filter_lag_value: float = filter_gain * filter_time / proportional_gain
    minimum: Var = control.parameter(stage_name + 'Minimum', output_minimum)
    maximum: Var = control.parameter(stage_name + 'Maximum', output_maximum)
    filtered: Var = control.lag(
        stage_name + 'Filtered', pi_output, filter_lag, filter_lag_value,
        pi_initial if filter_lag_value == 0.0 else output_initial,
        minimum, maximum,
    )
    return filtered
