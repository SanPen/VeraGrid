# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcIEEEAC6A excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcIEEEAC6AParameters:
    """IEEE AC6A settings from the exact CGMES scalar property surface."""

    __slots__ = (
        'ka', 'ta', 'tk', 'tb', 'tc', 'vamax', 'vamin', 'vrmax', 'vrmin',
        'te', 'kh', 'tj', 'th', 'vfelim', 'vhmax', 'kc', 'kd', 'ke', 've1',
        'seve1', 've2', 'seve2',
    )

    def __init__(
            self,
            ka: float = 536.0,
            ta: float = 0.086,
            tk: float = 0.18,
            tb: float = 9.0,
            tc: float = 3.0,
            vamax: float = 75.0,
            vamin: float = -75.0,
            vrmax: float = 44.0,
            vrmin: float = -36.0,
            te: float = 1.0,
            kh: float = 92.0,
            tj: float = 0.02,
            th: float = 0.08,
            vfelim: float = 19.0,
            vhmax: float = 75.0,
            kc: float = 0.173,
            kd: float = 1.91,
            ke: float = 1.6,
            ve1: float = 7.4,
            seve1: float = 0.214,
            ve2: float = 5.55,
            seve2: float = 0.044,
    ) -> None:
        """Store the 22 numeric settings, using local EA typical values.

        :param ka: Regulator gain.
        :param ta: Regulator lag time.
        :param tk: Regulator lead time.
        :param tb: Lead-lag denominator time.
        :param tc: Lead-lag numerator time.
        :param vamax: First regulator stage upper bound.
        :param vamin: First regulator stage lower bound.
        :param vrmax: Exciter input upper bound.
        :param vrmin: Exciter input lower bound.
        :param te: Exciter integration time.
        :param kh: Field-current limiter gain.
        :param tj: Field-current limiter lead time.
        :param th: Field-current limiter lag time.
        :param vfelim: Field-current limiter reference.
        :param vhmax: Limiter signal upper bound.
        :param kc: Rectifier loading coefficient.
        :param kd: Demagnetizing coefficient.
        :param ke: Exciter field constant.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        """
        self.ka: float = ka
        self.ta: float = ta
        self.tk: float = tk
        self.tb: float = tb
        self.tc: float = tc
        self.vamax: float = vamax
        self.vamin: float = vamin
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.te: float = te
        self.kh: float = kh
        self.tj: float = tj
        self.th: float = th
        self.vfelim: float = vfelim
        self.vhmax: float = vhmax
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.ve1: float = ve1
        self.seve1: float = seve1
        self.ve2: float = ve2
        self.seve2: float = seve2


def build_exc_i_e_e_e_a_c6_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcIEEEAC6AParameters | None = None,
) -> RmsModelTemplate:
    """Build IEEE AC6A regulator, limiter, exciter, and rectifier equations.

    :param vfactory: Factory that owns symbolic variables.
    :param name: Optional unique runtime name.
    :param parameters: Parsed RDF values; EA typicals apply when omitted.
    :return: Equation-backed AC6A graph exposing voltage, speed, Ifd, and Efd.
    :raises ValueError: Invalid time constants, limits, or saturation points.
    """
    settings: ExcIEEEAC6AParameters = (
        ExcIEEEAC6AParameters() if parameters is None else parameters
    )
    template_name: str = 'ExcIEEEAC6A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ta, settings.tk, settings.tb, settings.tc,
        settings.vamax, settings.vamin, settings.vrmax, settings.vrmin,
        settings.te, settings.kh, settings.tj, settings.th, settings.vfelim,
        settings.vhmax, settings.kc, settings.kd, settings.ke, settings.ve1,
        settings.seve1, settings.ve2, settings.seve2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcIEEEAC6A parameters must be finite')
    elif min(settings.ta, settings.tk, settings.tb, settings.tc, settings.te,
             settings.tj, settings.th) < 0.0:
        raise ValueError('ExcIEEEAC6A time constants must be nonnegative')
    elif settings.ta <= 0.0 or settings.te <= 0.0:
        raise ValueError('ExcIEEEAC6A TA and TE must be positive')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcIEEEAC6A zero TB requires zero TC')
    elif settings.th == 0.0 and settings.tj != 0.0:
        raise ValueError('ExcIEEEAC6A zero TH requires zero TJ')
    elif settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax:
        raise ValueError('ExcIEEEAC6A regulator limits are invalid')
    elif settings.vhmax <= 0.0 or settings.ke <= 0.0:
        raise ValueError('ExcIEEEAC6A field limits and KE must be positive')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcIEEEAC6A saturation points must be distinct and positive')
    elif settings.seve1 <= 0.0 or settings.seve2 <= 0.0:
        raise ValueError('ExcIEEEAC6A saturation values must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ta: Var = builder.parameter('TA', settings.ta)
    tk: Var = builder.parameter('TK', settings.tk)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    vamax: Var = builder.parameter('VAMAX', settings.vamax)
    vamin: Var = builder.parameter('VAMIN', settings.vamin)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    te: Var = builder.parameter('TE', settings.te)
    kh: Var = builder.parameter('KH', settings.kh)
    tj: Var = builder.parameter('TJ', settings.tj)
    th: Var = builder.parameter('TH', settings.th)
    vfelim: Var = builder.parameter('VFELIM', settings.vfelim)
    vhmax: Var = builder.parameter('VHMAX', settings.vhmax)
    kc: Var = builder.parameter('KC', settings.kc)
    kd: Var = builder.parameter('KD', settings.kd)
    ke: Var = builder.parameter('KE', settings.ke)
    ve1: Var = builder.parameter('VE1', settings.ve1)
    seve1: Var = builder.parameter('SEVE1', settings.seve1)
    ve2: Var = builder.parameter('VE2', settings.ve2)
    seve2: Var = builder.parameter('SEVE2', settings.seve2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    field_current: Var = builder.input('IfdPu', Const(0.0))
    speed: Var = builder.input('OmegaPu', Const(1.0))

    regulator_first_stage: Var = builder.bounded_lead_lag(
        'RegulatorFirstStagePu', ka * (reference - terminal_voltage), tk, ta,
        settings.tk, settings.ta, Const(0.0), vamin, vamax,
    )
    regulator_second_stage: Var = builder.lead_lag(
        'RegulatorSecondStagePu', regulator_first_stage, tc, tb,
        settings.tc, settings.tb, Const(0.0),
    )
    voltage_scaled_limits: Expr = sym.hard_sat(
        regulator_second_stage, terminal_voltage * vrmin, terminal_voltage * vrmax,
    )

    # The two loaded points define the IEEE exponential exciter characteristic.
    saturation_slope: Expr = sym.log(seve2 / seve1) / (ve2 - ve1)
    saturation_base: Expr = seve1 * sym.exp(-saturation_slope * ve1)
    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    saturation: Expr = saturation_base * sym.exp(saturation_slope * exciter_voltage)
    exciter_feedback: Expr = (ke + saturation) * exciter_voltage + kd * field_current
    limiter_error: Expr = vfelim - exciter_feedback
    limiter_filter: Var = builder.lead_lag(
        'FieldLimiterPu', limiter_error, tj, th, settings.tj, settings.th, Const(0.0),
    )
    limiter_output: Var = builder.algebraic(
        'FieldLimiterOutputPu', sym.hard_sat(kh * limiter_filter, Const(0.0), vhmax),
        Const(0.0),
    )
    exciter_input: Var = builder.algebraic(
        'ExciterInputPu', voltage_scaled_limits - limiter_output, Const(1.0),
    )
    builder.differential(
        exciter_voltage, (exciter_input - exciter_feedback) / te,
        Const(1.0), Const(0.0), Const(1e12),
    )

    # IEEE AC6A output includes rectifier commutation and shaft-speed correction.
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    rectifier_output: Expr = exciter_voltage * sym.f_exc(rectifier_loading)
    field_voltage: Var = builder.algebraic(
        'EfdPu', rectifier_output * speed, Const(1.0),
    )
    template: RmsModelTemplate = builder.finish(
        (field_voltage,), 'CGMES ExcIEEEAC6A excitation system',
    )
    for parameter_name in (
            'enabled', 'ka', 'ta', 'tk', 'tb', 'tc', 'vamax', 'vamin', 'vrmax',
            'vrmin', 'te', 'kh', 'tj', 'th', 'vfelim', 'vhmax', 'kc', 'kd',
            'ke', 've1', 'seve1', 've2', 'seve2',
    ):
        variable_name: str = f'ExcIEEEAC6A.{parameter_name}_{template_name}'
        parameter_variable: Var = vfactory.add_var(variable_name)
        template.block.event_dict[parameter_variable] = vfactory.add_const(
            value=None, name=variable_name,
        )
    return template
