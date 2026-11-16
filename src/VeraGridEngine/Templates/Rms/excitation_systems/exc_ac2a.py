# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcAC2A alternator-supplied rectifier excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC2AParameters:
    """CGMES ExcAC2A regulator, limiter, exciter, and rectifier settings."""

    __slots__ = (
        'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'kb', 'kb1', 'vrmax', 'vrmin',
        'te', 'vfemax', 'kh', 'kf', 'kl', 'vlr', 'kl1', 'ks', 'tf', 'kc',
        'kd', 'ke', 've1', 'seve1', 've2', 'seve2', 'hvgate', 'lvgate',
    )

    def __init__(
            self,
            tb: float = 0.0,
            tc: float = 0.0,
            ka: float = 400.0,
            ta: float = 0.02,
            vamax: float = 8.0,
            vamin: float = -8.0,
            kb: float = 25.0,
            kb1: float = 25.0,
            vrmax: float = 105.0,
            vrmin: float = -95.0,
            te: float = 0.6,
            vfemax: float = 4.4,
            kh: float = 1.0,
            kf: float = 0.03,
            kl: float = 10.0,
            vlr: float = 4.4,
            kl1: float = 1.0,
            ks: float = 0.0,
            tf: float = 1.0,
            kc: float = 0.28,
            kd: float = 0.35,
            ke: float = 1.0,
            ve1: float = 4.4,
            seve1: float = 0.037,
            ve2: float = 3.3,
            seve2: float = 0.012,
            hvgate: bool = True,
            lvgate: bool = True,
    ) -> None:
        """Store canonical CGMES ExcAC2A parameters.

        :param tb: Regulator lead-lag denominator time in seconds.
        :param tc: Regulator lead-lag numerator time in seconds.
        :param ka: Regulator gain.
        :param ta: Regulator amplifier time in seconds.
        :param vamax: Amplifier upper limit.
        :param vamin: Amplifier lower limit.
        :param kb: First exciter field-current controller gain.
        :param kb1: Alternative second controller gain.
        :param vrmax: Exciter regulator upper limit.
        :param vrmin: Exciter regulator lower limit.
        :param te: Exciter time constant in seconds.
        :param vfemax: Exciter field current limit reference; zero disables its Ve cap.
        :param kh: Exciter field current feedback gain.
        :param kf: Stabilizer feedback gain.
        :param kl: Low-voltage gate field-current limiter gain.
        :param vlr: Maximum exciter field current.
        :param kl1: Alternative low-voltage gate gain.
        :param ks: Generator speed multiplier selector.
        :param tf: Stabilizer time constant in seconds.
        :param kc: Rectifier commutating reactance factor.
        :param kd: Exciter demagnetizing factor.
        :param ke: Exciter field constant.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        :param hvgate: Enable the high voltage gate.
        :param lvgate: Enable the low voltage gate.
        """
        self.tb: float = tb
        self.tc: float = tc
        self.ka: float = ka
        self.ta: float = ta
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.kb: float = kb
        self.kb1: float = kb1
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.te: float = te
        self.vfemax: float = vfemax
        self.kh: float = kh
        self.kf: float = kf
        self.kl: float = kl
        self.vlr: float = vlr
        self.kl1: float = kl1
        self.ks: float = ks
        self.tf: float = tf
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2
        self.hvgate: bool = hvgate
        self.lvgate: bool = lvgate


def build_exc_a_c2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC2AParameters | None = None,
) -> RmsModelTemplate:
    """Build ExcAC2A regulator, exciter, limiter, and rectifier equations.

    :param vfactory: Factory that owns the symbolic graph.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Executable ExcAC2A model with machine and limiter ports.
    :raises ValueError: Invalid times, limits, or saturation points.
    """
    settings: ExcAC2AParameters = ExcAC2AParameters() if parameters is None else parameters
    template_name: str = 'ExcAC2A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tb, settings.tc, settings.ka, settings.ta, settings.vamax,
        settings.vamin, settings.kb, settings.kb1, settings.vrmax, settings.vrmin,
        settings.te, settings.vfemax, settings.kh, settings.kf, settings.kl,
        settings.vlr, settings.kl1, settings.ks, settings.tf, settings.kc,
        settings.kd, settings.ke, settings.ve1, settings.seve1, settings.ve2,
        settings.seve2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC2A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcAC2A times must be nonnegative and T_E must be positive')
    elif settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcAC2A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcAC2A requires zero lead when T_B is zero')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcAC2A nonzero K_F requires positive T_F')
    elif (settings.seve1 == 0.0) != (settings.seve2 == 0.0):
        raise ValueError('ExcAC2A saturation requires both saturation values or neither')
    elif settings.seve1 == 0.0:
        pass
    elif (
            settings.ve1 <= 0.0 or settings.ve2 <= 0.0
            or settings.ve1 == settings.ve2
            or settings.seve1 < 0.0 or settings.seve2 < 0.0
    ):
        raise ValueError('ExcAC2A saturation needs distinct positive voltage points')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    kb: Var = builder.parameter('KB', settings.kb)
    kb1: Var = builder.parameter('KB1', settings.kb1)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    te: Var = builder.parameter('TE', settings.te)
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    kh: Var = builder.parameter('KH', settings.kh)
    kf: Var = builder.parameter('KF', settings.kf)
    kl: Var = builder.parameter('KL', settings.kl)
    vlr: Var = builder.parameter('VLR', settings.vlr)
    kl1: Var = builder.parameter('KL1', settings.kl1)
    ks: Var = builder.parameter('KS', settings.ks)
    tf: Var = builder.parameter('TF', settings.tf)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    ke: Var = builder.parameter('KE', settings.ke)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    speed: Var | None = None
    if settings.ks != 0.0:
        speed = builder.input('OmegaPu', Const(1.0))
    else:
        pass
    high_voltage_gate: Var = builder.input('VuelPu', Const(0.0))
    low_voltage_gate: Var = builder.input('VoelPu', Const(0.0))

    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    saturation: Expr = Const(0.0)
    if settings.seve1 > 0.0 and settings.seve2 > 0.0:
        saturation_b: float = math.log(settings.seve2 / settings.seve1) / (settings.ve2 - settings.ve1)
        saturation_a: float = settings.seve1 * math.exp(-saturation_b * settings.ve1)
        saturation = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_voltage)
    else:
        pass
    exciter_voltage_feedback: Expr = (ke + saturation) * exciter_voltage + kd * field_current
    feedback: Var
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', exciter_voltage_feedback, tf, settings.tf,
            Const(settings.kf / settings.tf), exciter_voltage_feedback,
        )
    else:
        feedback = builder.algebraic('FeedbackPu', Const(0.0), Const(0.0))
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback, Const(0.0),
    )
    lead_lag: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    amplifier: Var = builder.lag(
        'AmplifierPu', ka * lead_lag, ta, settings.ta, Const(0.0), vamin, vamax,
    )

    regulator_input: Var = vfactory.add_var(f'RegulatorInputPu_{template_name}')
    builder.block.algebraic_vars.append(regulator_input)
    limiter_signal: Expr = kl * (vlr - kl1 * regulator_input)
    first_regulator_stage: Expr = kb * (amplifier - kh * exciter_voltage_feedback)
    gated_signal: Expr = first_regulator_stage
    if settings.hvgate:
        gated_signal = sym.max(gated_signal, high_voltage_gate)
    else:
        pass
    if settings.lvgate:
        gated_signal = sym.min(gated_signal, low_voltage_gate + limiter_signal)
    else:
        pass

    builder.block.algebraic_eqs.append(
        regulator_input - sym.hard_sat(kb1 * gated_signal, vrmin, vrmax),
    )
    builder.block.init_eqs[regulator_input] = Const(0.0)
    exciter_voltage_feedback: Expr = (ke + saturation) * exciter_voltage + kd * field_current
    exciter_derivative: Expr = (regulator_input - exciter_voltage_feedback) / te
    exciter_derivative = (
        exciter_derivative * sym.heaviside(exciter_voltage - Const(1e-9))
        + sym.max(exciter_derivative, Const(0.0))
        * (Const(1.0) - sym.heaviside(exciter_voltage - Const(1e-9)))
    )
    ve_upper: Expr = Const(1e12)
    if settings.vfemax != 0.0:
        ve_upper = sym.max(
            (vfemax - kd * field_current) / (ke + saturation), Const(0.0),
        )
    else:
        pass
    builder.differential(
        exciter_voltage, exciter_derivative, Const(1.0), Const(0.0), ve_upper,
    )

    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    speed_correction: Expr = Const(1.0)
    if speed is not None:
        speed_correction = Const(1.0) + ks * (speed - Const(1.0))
    else:
        pass
    rectifier_output: Expr = exciter_voltage * sym.f_exc(rectifier_loading) * speed_correction
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - rectifier_output)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcAC2A excitation system',
    )

    return template
