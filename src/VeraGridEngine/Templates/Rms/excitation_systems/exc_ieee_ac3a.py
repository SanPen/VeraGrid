# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC3A self-excited alternator exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC3AParameters:
    """CGMES AC3A regulator, self-excited field, saturation, and rectifier data."""

    __slots__ = (
        'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'vemin', 'kr', 'kf',
        'tf', 'kn', 'efdn', 'kc', 'kd', 'ke', 'vfemax', 've1', 'seve1',
        've2', 'seve2',
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
            vfemax: float = 16.0,
            ve1: float = 6.24,
            seve1: float = 1.143,
            ve2: float = 4.68,
            seve2: float = 0.1,
    ) -> None:
        """Store CGMES model values in per-unit and seconds.

        :param tb: Phase-compensator denominator time.
        :param tc: Phase-compensator numerator time.
        :param ka: Regulator gain.
        :param ta: Regulator time constant.
        :param vamax: Regulator output upper limit.
        :param vamin: Regulator output lower limit.
        :param te: Rotating exciter integration time.
        :param vemin: Minimum exciter internal field voltage.
        :param kr: Self-excitation multiplier gain.
        :param kf: Low-field stabilizer feedback slope.
        :param tf: Stabilizer washout time.
        :param kn: High-field stabilizer feedback slope.
        :param efdn: Field-voltage feedback slope transition.
        :param kc: Rectifier commutation loading factor.
        :param kd: Exciter demagnetizing factor.
        :param ke: Self-excited field constant.
        :param vfemax: Exciter field-current equivalent ceiling.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
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
        self.vfemax: float = vfemax
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2


def build_exc_i_e_e_e_a_c3_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC3AParameters | None = None,
) -> RmsModelTemplate:
    """Build AC3A regulator, self-excited exciter, and rectifier equations.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed RDF properties used for equations and branch selection.
    :return: Executable AC3A excitation model with voltage, PSS, and Ifd ports.
    :raises ValueError: Nonfinite values, invalid limits, or invalid characteristic points.
    """
    settings: ExcIEEEAC3AParameters = (
        ExcIEEEAC3AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC3A' if name is None else name
    values: tuple[float, ...] = (
        settings.tb, settings.tc, settings.ka, settings.ta, settings.vamax,
        settings.vamin, settings.te, settings.vemin, settings.kr, settings.kf,
        settings.tf, settings.kn, settings.efdn, settings.kc, settings.kd,
        settings.ke, settings.vfemax, settings.ve1, settings.seve1,
        settings.ve2, settings.seve2,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEAC3A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta) < 0.0 or settings.te <= 0.0 or settings.tf <= 0.0:
        raise ValueError('ExcIEEEAC3A times must be nonnegative; T_E and T_F must be positive')
    elif settings.vamin >= settings.vamax or settings.vemin < 0.0:
        raise ValueError('ExcIEEEAC3A voltage limits are inconsistent')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEAC3A requires zero lead when T_B is zero')
    elif settings.kr <= 0.0 or settings.efdn <= 0.0 or settings.vfemax <= 0.0:
        raise ValueError('ExcIEEEAC3A requires positive K_R, EFDN, and VFEMAX')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcIEEEAC3A saturation needs distinct positive voltage points')
    elif settings.seve1 <= 0.0 or settings.seve2 <= 0.0:
        raise ValueError('ExcIEEEAC3A saturation values must be positive')
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
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))

    # The Efd-dependent slope changes continuously at EFDN before the washout.
    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback_signal: Expr = (
        kf * field_voltage + (kn - kf) * sym.max(field_voltage - efdn, Const(0.0))
    )
    feedback: Var = builder.washout(
        'FeedbackPu', feedback_signal, tf, settings.tf, Const(1.0) / tf,
        Const(settings.kf + (settings.kn - settings.kf) * max(1.0 - settings.efdn, 0.0)),
    )
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback, Const(0.0),
    )
    phase_compensation: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    regulator: Var = builder.lag(
        'RegulatorPu', ka * phase_compensation, ta, settings.ta, Const(0.0), vamin, vamax,
    )

    # Two saturation points preserve the nonlinear rotating-field characteristic.
    saturation_b: Expr = sym.log(seve2 / seve1) / (ve2 - ve1)
    saturation_a: Expr = seve1 * sym.exp(-saturation_b * ve1)
    saturation: Expr = saturation_a * sym.exp(saturation_b * exciter_voltage)
    rectifier_ratio: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    rectifier_factor: Expr = sym.f_exc(rectifier_ratio)
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - exciter_voltage * rectifier_factor)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    field_forcing: Expr = kr * field_voltage * regulator
    field_losses: Expr = (ke + saturation) * exciter_voltage + kd * field_current
    raw_derivative: Expr = (field_forcing - field_losses) / te
    current_equivalent: Expr = field_losses
    lower_stop: Expr = (
        (Const(1.0) - sym.heaviside(exciter_voltage - vemin))
        * sym.heaviside(-raw_derivative)
    )
    upper_stop: Expr = (
        (Const(1.0) - sym.heaviside(vfemax - current_equivalent))
        * sym.heaviside(raw_derivative)
    )
    limited_derivative: Expr = raw_derivative * (Const(1.0) - lower_stop) * (Const(1.0) - upper_stop)
    builder.differential(exciter_voltage, limited_derivative, Const(1.0))
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEAC3A self-excited alternator excitation system',
    )

    # Keep the exact RDF property names available to event-based model updates.
    for parameter_name in (
            'enabled', 'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'te', 'vemin',
            'kr', 'kf', 'tf', 'kn', 'efdn', 'kc', 'kd', 'ke', 'vfemax', 've1',
            'seve1', 've2', 'seve2',
    ):
        variable_name: str = f'ExcIEEEAC3A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
