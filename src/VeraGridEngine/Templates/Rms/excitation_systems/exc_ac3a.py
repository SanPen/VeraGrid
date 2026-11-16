# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcAC3A alternator-supplied rectifier excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC3AParameters:
    """CGMES ExcAC3A regulator, field feedback, limiter, and rectifier settings."""

    __slots__ = (
        'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'vemin', 'kr', 'kf',
        'tf', 'kn', 'efdn', 'kc', 'kd', 'ke', 'klv', 'kf1', 'kf2', 'ks',
        'vfemax', 've1', 'seve1', 've2', 'seve2', 'vlv',
    )

    def __init__(
            self,
            tb: float = 0.0,
            tc: float = 0.0,
            ka: float = 45.62,
            ta: float = 0.013,
            vamax: float = 1.0,
            vamin: float = -0.95,
            te: float = 1.17,
            vemin: float = 0.1,
            kr: float = 3.77,
            kf: float = 0.143,
            tf: float = 1.0,
            kn: float = 0.05,
            efdn: float = 2.36,
            kc: float = 0.104,
            kd: float = 0.499,
            ke: float = 1.0,
            klv: float = 0.194,
            kf1: float = 1.0,
            kf2: float = 0.0,
            ks: float = 0.0,
            vfemax: float = 16.0,
            ve1: float = 6.24,
            seve1: float = 1.143,
            ve2: float = 4.68,
            seve2: float = 0.1,
            vlv: float = 0.79,
    ) -> None:
        """Store the canonical ExcAC3A fields used by the equation graph.

        :param tb: Regulator lead-lag denominator time in seconds.
        :param tc: Regulator lead-lag numerator time in seconds.
        :param ka: Regulator amplifier gain.
        :param ta: Regulator amplifier time in seconds.
        :param vamax: Amplifier upper limit.
        :param vamin: Amplifier lower limit.
        :param te: Exciter time constant in seconds.
        :param vemin: Exciter field-voltage lower limit.
        :param kr: Exciter regulator forcing gain.
        :param kf: Low-field feedback slope.
        :param tf: Feedback washout time in seconds.
        :param kn: High-field feedback slope.
        :param efdn: Field voltage where the feedback slope changes.
        :param kc: Rectifier commutating reactance factor.
        :param kd: Exciter demagnetizing factor.
        :param ke: Exciter field constant.
        :param klv: Minimum-voltage limiter gain.
        :param kf1: Feedback gain at the regulator input.
        :param kf2: Feedback gain at the voltage-error input.
        :param ks: Generator speed multiplier selector.
        :param vfemax: Exciter field-current limit reference; zero disables its cap.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        :param vlv: Minimum field-voltage limiter reference.
        """
        self.tb: float = tb
        self.tc: float = tc
        self.ka: float = ka
        self.ta: float = ta
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.te: float = te
        self.vemin: float = vemin
        self.kr: float = kr
        self.kf: float = kf
        self.tf: float = tf
        self.kn: float = kn
        self.efdn: float = efdn
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.klv: float = klv
        self.kf1: float = kf1
        self.kf2: float = kf2
        self.ks: float = ks
        self.vfemax: float = vfemax
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2
        self.vlv: float = vlv


def build_exc_a_c3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC3AParameters | None = None,
) -> RmsModelTemplate:
    """Build ExcAC3A regulator, feedback, field, and rectifier equations.

    The stabilizing signal is the continuous piecewise feedback curve
    ``kf*Efd+(kn-kf)*max(Efd-efdn, 0)``.  The amplifier output is multiplied by
    ``kr*Efd`` to retain alternator-supplied excitation behavior.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES settings.
    :return: Executable ExcAC3A model with machine and limiter ports.
    :raises ValueError: Invalid times, limits, or saturation points.
    """
    settings: ExcAC3AParameters = ExcAC3AParameters() if parameters is None else parameters
    template_name: str = 'ExcAC3A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.tb, settings.tc, settings.ka, settings.ta, settings.vamax,
        settings.vamin, settings.te, settings.vemin, settings.kr, settings.kf,
        settings.tf, settings.kn, settings.efdn, settings.kc, settings.kd,
        settings.ke, settings.klv, settings.kf1, settings.kf2, settings.ks,
        settings.vfemax, settings.ve1, settings.seve1, settings.ve2,
        settings.seve2, settings.vlv,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC3A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcAC3A times must be nonnegative and T_E must be positive')
    elif settings.vamin >= settings.vamax or settings.vemin < 0.0:
        raise ValueError('ExcAC3A voltage limits are invalid')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcAC3A requires zero lead when T_B is zero')
    elif settings.tf == 0.0 and (settings.kf1 != 0.0 or settings.kf2 != 0.0):
        raise ValueError('ExcAC3A nonzero feedback gains require positive T_F')
    elif settings.efdn <= 0.0 or settings.kr <= 0.0 or settings.ke <= 0.0:
        raise ValueError('ExcAC3A EFDN, KR, and KE must be positive')
    elif (settings.seve1 == 0.0) != (settings.seve2 == 0.0):
        raise ValueError('ExcAC3A saturation requires both saturation values or neither')
    elif settings.seve1 == 0.0:
        pass
    elif (
            settings.ve1 <= 0.0 or settings.ve2 <= 0.0
            or settings.ve1 == settings.ve2
            or settings.seve1 < 0.0 or settings.seve2 < 0.0
    ):
        raise ValueError('ExcAC3A saturation needs distinct positive voltage points')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    te: Var = builder.parameter('TE', settings.te)
    vemin: Var = builder.parameter('VEMIN', settings.vemin)
    kr: Var = builder.parameter('KR', settings.kr)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    kn: Var = builder.parameter('KN', settings.kn)
    efdn: Var = builder.parameter('EFDN', settings.efdn)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    ke: Var = builder.parameter('KE', settings.ke)
    klv: Var = builder.parameter('KLV', settings.klv)
    kf1: Var = builder.parameter('KF1', settings.kf1)
    kf2: Var = builder.parameter('KF2', settings.kf2)
    ks: Var = builder.parameter('KS', settings.ks)
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    vlv: Var = builder.parameter('VLV', settings.vlv)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    high_voltage_gate: Var = builder.input('VuelPu', Const(0.0))
    speed: Var | None = None
    if settings.ks != 0.0:
        speed = builder.input('OmegaPu', Const(1.0))
    else:
        pass

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
    nonlinear_feedback: Expr = kf * field_voltage + (kn - kf) * sym.max(
        field_voltage - efdn, Const(0.0),
    )
    feedback: Var
    if settings.tf > 0.0 and (settings.kf1 != 0.0 or settings.kf2 != 0.0):
        feedback = builder.washout(
            'FeedbackPu', nonlinear_feedback, tf, settings.tf,
            Const(1.0 / settings.tf), nonlinear_feedback,
        )
    else:
        feedback = builder.algebraic('FeedbackPu', Const(0.0), Const(0.0))
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - kf2 * feedback, Const(0.0),
    )
    lead_lag: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    regulator_error: Expr = lead_lag - kf1 * feedback
    minimum_field_gate: Expr = klv * (vlv - field_voltage)
    gated_error: Expr = sym.max(regulator_error, minimum_field_gate)
    gated_error = sym.max(gated_error, high_voltage_gate)
    amplifier: Var = builder.lag(
        'AmplifierPu', ka * gated_error, ta, settings.ta, Const(0.0), vamin, vamax,
    )
    forcing: Expr = kr * field_voltage * amplifier
    field_derivative: Expr = (forcing - exciter_voltage_feedback) / te
    upper_field_limit: Expr = Const(1e12)
    if settings.vfemax != 0.0:
        upper_field_limit = sym.max(
            (vfemax - kd * field_current) / (ke + saturation), Const(0.0),
        )
    else:
        pass
    builder.differential(
        exciter_voltage,
        field_derivative,
        Const(1.0),
        vemin,
        upper_field_limit,
    )
    builder.block.inequalities.extend((
        amplifier >= vamin,
        amplifier <= vamax,
        exciter_voltage >= vemin,
        field_current >= Const(0.0),
    ))
    if settings.vfemax != 0.0:
        builder.block.inequalities.append(exciter_voltage <= upper_field_limit)
    else:
        pass
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
        (field_voltage,), 'CGMES ExcAC3A excitation system',
    )
    return template
