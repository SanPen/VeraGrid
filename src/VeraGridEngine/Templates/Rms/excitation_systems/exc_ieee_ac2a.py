# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC2A alternator-rectifier exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC2AParameters:
    """IEEE AC2A regulator, exciter current limit, and rectifier settings."""

    __slots__ = (
        'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'kb', 'vrmax', 'vrmin',
        'te', 'vfemax', 'kh', 'kf', 'tf', 'kc', 'kd', 'ke', 've1', 'seve1',
        've2', 'seve2',
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
            vrmax: float = 105.0,
            vrmin: float = -95.0,
            te: float = 0.6,
            vfemax: float = 4.4,
            kh: float = 1.0,
            kf: float = 0.03,
            tf: float = 1.0,
            kc: float = 0.28,
            kd: float = 0.35,
            ke: float = 1.0,
            ve1: float = 4.4,
            seve1: float = 0.037,
            ve2: float = 3.3,
            seve2: float = 0.012,
    ) -> None:
        """Store CGMES values in their declared per-unit and time units.

        :param tb: Voltage regulator denominator time.
        :param tc: Voltage regulator numerator time.
        :param ka: Voltage regulator gain.
        :param ta: Voltage regulator time constant.
        :param vamax: Phase-compensator upper limit.
        :param vamin: Phase-compensator lower limit.
        :param kb: Second-stage regulator gain.
        :param vrmax: Regulator upper limit.
        :param vrmin: Regulator lower limit.
        :param te: Exciter integration time.
        :param vfemax: Exciter field-current limit reference.
        :param kh: Exciter field-current feedback gain.
        :param kf: Stabilizer feedback gain.
        :param tf: Stabilizer feedback time.
        :param kc: Rectifier loading factor.
        :param kd: Exciter demagnetizing factor.
        :param ke: Self-excited field constant.
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
        self.kb: float = kb
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.te: float = te
        self.vfemax: float = vfemax
        self.kh: float = kh
        self.kf: float = kf
        self.tf: float = tf
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2


def build_exc_i_e_e_e_a_c2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC2AParameters | None = None,
) -> RmsModelTemplate:
    """Build the AC2A voltage regulator, exciter, and rectifier equations.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional unique runtime model name.
    :param parameters: Parsed CGMES values used to select stage topology.
    :return: Executable AC2A excitation model with voltage, PSS, and Ifd inputs.
    :raises ValueError: Invalid times, limits, or saturation points.
    """
    settings: ExcIEEEAC2AParameters = (
        ExcIEEEAC2AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC2A' if name is None else name
    values: tuple[float, ...] = (
        settings.tb, settings.tc, settings.ka, settings.ta, settings.vamax,
        settings.vamin, settings.kb, settings.vrmax, settings.vrmin,
        settings.te, settings.vfemax, settings.kh, settings.kf, settings.tf,
        settings.kc, settings.kd, settings.ke, settings.ve1, settings.seve1,
        settings.ve2, settings.seve2,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('ExcIEEEAC2A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcIEEEAC2A times must be nonnegative and T_E positive')
    elif settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEAC2A lower limits must be below upper limits')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEAC2A requires zero lead when T_B is zero')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcIEEEAC2A nonzero K_F requires positive T_F')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcIEEEAC2A saturation needs distinct positive voltage points')
    elif settings.seve1 <= 0.0 or settings.seve2 <= 0.0:
        raise ValueError('ExcIEEEAC2A saturation values must be positive')
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
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    te: Var = builder.parameter('TE', settings.te)
    vfemax: Var = builder.parameter('VFEMAX', settings.vfemax)
    kh: Var = builder.parameter('KH', settings.kh)
    kf: Var = builder.parameter('KF', settings.kf)
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

    # Saturation and demagnetizing feedback define the VFE signal used throughout the AC2A diagram.
    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    saturation_b: Expr = sym.log(seve2 / seve1) / (ve2 - ve1)
    saturation_a: Expr = seve1 * sym.exp(-saturation_b * ve1)
    saturation: Expr = saturation_a * sym.exp(saturation_b * exciter_voltage)
    field_voltage_feedback: Expr = (
        (ke + saturation) * exciter_voltage + kd * field_current
    )
    feedback: Expr = Const(0.0)
    if settings.kf != 0.0:
        feedback = builder.washout(
            'FeedbackPu', field_voltage_feedback, tf, settings.tf,
            Const(settings.kf / settings.tf), field_voltage_feedback,
        )
    else:
        pass
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback, Const(0.0),
    )
    phase_compensation: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    amplifier_input: Var = builder.algebraic(
        'AmplifierInputPu', sym.hard_sat(phase_compensation, vamin, vamax), Const(0.0),
    )
    first_regulator: Var = builder.lag(
        'RegulatorPu', ka * amplifier_input, ta, settings.ta, Const(0.0), vrmin, vrmax,
    )
    second_regulator: Var = builder.algebraic(
        'SecondRegulatorPu', kb * (first_regulator - kh * field_voltage_feedback), Const(0.0),
    )

    exciter_derivative: Expr = (second_regulator - field_voltage_feedback) / te
    field_current_equivalent: Expr = field_voltage_feedback
    lower_stop: Expr = (
        (Const(1.0) - sym.heaviside(exciter_voltage))
        * sym.heaviside(-exciter_derivative)
    )
    upper_stop: Expr = (
        (Const(1.0) - sym.heaviside(vfemax - field_current_equivalent))
        * sym.heaviside(exciter_derivative)
    )
    field_derivative: Expr = (
        exciter_derivative * (Const(1.0) - lower_stop) * (Const(1.0) - upper_stop)
    )
    builder.differential(exciter_voltage, field_derivative, Const(1.0))
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    field_voltage: Var = builder.algebraic(
        'EfdPu', exciter_voltage * sym.f_exc(rectifier_loading), Const(1.0),
    )
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEAC2A excitation system',
    )

    # Preserve every canonical RDF scalar as an editable runtime event parameter.
    for parameter_name in (
            'enabled', 'tb', 'tc', 'ka', 'ta', 'vamax', 'vamin', 'kb', 'vrmax',
            'vrmin', 'te', 'vfemax', 'kh', 'kf', 'tf', 'kc', 'kd', 'ke', 've1',
            'seve1', 've2', 'seve2',
    ):
        variable_name: str = f'ExcIEEEAC2A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=None, name=variable_name)
    return template
