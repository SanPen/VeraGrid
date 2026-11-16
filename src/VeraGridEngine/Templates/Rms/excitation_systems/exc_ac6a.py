# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAC6A alternator rectifier excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC6AParameters:
    """Canonical numeric settings for the CGMES ExcAC6A block diagram."""

    __slots__ = (
        'ka', 'ks', 'ta', 'tk', 'tb', 'tc', 'vamax', 'vamin', 'vrmax', 'vrmin',
        'te', 'kh', 'tj', 'th', 'vfelim', 'vhmax', 'kc', 'kd', 'ke', 've1',
        'seve1', 've2', 'seve2',
    )

    def __init__(
            self,
            ka: float = 536.0,
            ks: float = 0.0,
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
        """Store the RDF numeric values and EA typical values.

        :param ka: Regulator gain.
        :param ks: Generator-speed correction gain.
        :param ta: Regulator lag time.
        :param tk: Regulator lead time.
        :param tb: Regulator lead-lag denominator time.
        :param tc: Regulator lead-lag numerator time.
        :param vamax: First regulator output upper bound.
        :param vamin: First regulator output lower bound.
        :param vrmax: Exciter input upper bound.
        :param vrmin: Exciter input lower bound.
        :param te: Exciter integration time.
        :param kh: Field-current limiter gain.
        :param tj: Limiter lead time.
        :param th: Limiter lag time.
        :param vfelim: Field-current limiter reference.
        :param vhmax: Limiter output upper bound.
        :param kc: Rectifier commutating-reactance factor.
        :param kd: Demagnetizing factor.
        :param ke: Exciter field constant.
        :param ve1: First saturation voltage point.
        :param seve1: Saturation at ``ve1``.
        :param ve2: Second saturation voltage point.
        :param seve2: Saturation at ``ve2``.
        """
        self.ka: float = ka
        self.ks: float = ks
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


def build_exc_a_c6_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC6AParameters | None = None,
) -> RmsModelTemplate:
    """Build the AC6A regulator, current limiter, exciter, and rectifier equations.

    :param vfactory: Factory that owns the symbolic variables.
    :param name: Optional runtime template name.
    :param parameters: Parsed canonical CGMES numeric settings.
    :return: Equation-backed AC6A with terminal voltage, field current, and speed ports.
    :raises ValueError: If a time, limit, or saturation point is invalid.
    """
    settings: ExcAC6AParameters = ExcAC6AParameters() if parameters is None else parameters
    template_name: str = 'ExcAC6A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ks, settings.ta, settings.tk, settings.tb, settings.tc,
        settings.vamax, settings.vamin, settings.vrmax, settings.vrmin, settings.te,
        settings.kh, settings.tj, settings.th, settings.vfelim, settings.vhmax,
        settings.kc, settings.kd, settings.ke, settings.ve1, settings.seve1,
        settings.ve2, settings.seve2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC6A parameters must be finite')
    elif min(settings.ta, settings.tk, settings.tb, settings.tc, settings.te, settings.tj, settings.th) < 0.0:
        raise ValueError('ExcAC6A times must be nonnegative')
    elif settings.ta <= 0.0 or settings.te <= 0.0:
        raise ValueError('ExcAC6A T_A and T_E must be positive')
    elif settings.vamin >= settings.vamax or settings.vrmin >= settings.vrmax or settings.vhmax <= 0.0:
        raise ValueError('ExcAC6A regulator and limiter bounds are invalid')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcAC6A requires zero lead when T_B is zero')
    elif settings.th == 0.0 and settings.tj != 0.0:
        raise ValueError('ExcAC6A requires zero limiter lead when T_H is zero')
    elif settings.ve1 <= 0.0 or settings.ve2 <= 0.0 or settings.ve1 == settings.ve2:
        raise ValueError('ExcAC6A saturation voltage points must be distinct and positive')
    elif settings.seve1 <= 0.0 or settings.seve2 <= 0.0 or settings.ke <= 0.0:
        raise ValueError('ExcAC6A saturation values and K_E must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ks: Var = builder.parameter('KS', settings.ks)
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

    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    limiter_output: Var = vfactory.add_var(f'LimiterPu_{template_name}')
    regulator_output: Var = builder.bounded_lead_lag(
        'RegulatorLeadPu', ka * (reference - terminal_voltage), tk, ta,
        settings.tk, settings.ta, Const(0.0), vamin, vamax,
    )
    regulator_lead_lag: Var = builder.lead_lag(
        'RegulatorLeadLagPu', regulator_output, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    saturation_b: float = math.log(settings.seve2 / settings.seve1) / (settings.ve2 - settings.ve1)
    saturation_a: float = settings.seve1 * math.exp(-saturation_b * settings.ve1)
    saturation: Expr = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_voltage)
    exciter_feedback: Expr = (ke + saturation) * exciter_voltage + kd * field_current
    field_error: Expr = exciter_feedback - vfelim
    limiter_filtered: Var = builder.lead_lag(
        'FieldLimiterLeadLagPu', field_error, tj, th, settings.tj, settings.th, Const(0.0),
    )
    builder.block.algebraic_vars.append(limiter_output)
    builder.block.algebraic_eqs.append(
        limiter_output - sym.hard_sat(kh * limiter_filtered, Const(0.0), vhmax)
    )
    exciter_input: Var = builder.algebraic(
        'ExciterInputPu',
        sym.hard_sat(regulator_lead_lag, vrmin, vrmax) - limiter_output,
        Const(1.0),
    )
    exciter_derivative: Expr = (exciter_input - exciter_feedback) / te
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0), Const(0.0), Const(1e12))
    rectifier_loading: Expr = sym.safe_divide(kc * field_current, exciter_voltage, Const(1.0))
    rectifier_output: Expr = exciter_voltage * sym.f_exc(rectifier_loading)
    speed_factor: Expr = Const(1.0) + ks * (speed - Const(1.0))
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - rectifier_output * speed_factor)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    return builder.finish((field_voltage,), 'CGMES ExcAC6A alternator rectifier excitation system')
