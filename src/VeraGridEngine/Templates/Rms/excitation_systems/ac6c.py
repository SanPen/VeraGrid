# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""Two-stage brushless voltage regulation with bounded field forcing and field-current feedback."""
from __future__ import annotations

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import _quadratic_saturation_coefficients
from VeraGridEngine.Templates.Rms.excitation_systems.ac8b import initial_internal_exciter_voltage
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class FieldLimitVoltage(Enum):
    """Select whether regulator forcing limits follow live terminal magnitude."""

    FIXED = 0
    TERMINAL = 1


class Ac6cLimiterLocation(Enum):
    """Select signed error addition or bounded-regulator takeover."""

    ERROR_SUM = 1
    REGULATOR_GATE = 2


class Ac6cParameters:
    """Physical two-stage regulator, feedback and rotating-field coefficients."""

    __slots__ = ('tr','ka','ta','tk','tb','tc','vamax','vamin','vrmax','vrmin','te',
                 'vfelim','kh','vhmax','th','tj','kc','kd','ke','e1','se1','e2','se2',
                 'vfemax','vemin','minimum_location','maximum_location','limit_voltage')

    def __init__(self, tr: float = .02, ka: float = 20., ta: float = .05, tk: float = .02,
                 tb: float = .05, tc: float = .02, vamax: float = 5., vamin: float = -5.,
                 vrmax: float = 5., vrmin: float = -5., te: float = .5, vfelim: float = 2.,
                 kh: float = .2, vhmax: float = 2., th: float = .1, tj: float = .05,
                 kc: float = .1, kd: float = .1, ke: float = 1., e1: float = 3., se1: float = .1,
                 e2: float = 4., se2: float = .3, vfemax: float = 5., vemin: float = 0.,
                 minimum_location: Ac6cLimiterLocation = Ac6cLimiterLocation.ERROR_SUM,
                 maximum_location: Ac6cLimiterLocation = Ac6cLimiterLocation.ERROR_SUM,
                 limit_voltage: FieldLimitVoltage = FieldLimitVoltage.TERMINAL) -> None:
        """Store independent physical settings and structural limiter choices.

        :param tr: Terminal-voltage sensing time, seconds.
        :param ka: Positive regulator gain.
        :param ta: First lead-lag denominator time, seconds.
        :param tk: First lead-lag numerator time, seconds.
        :param tb: Bounded second lead-lag denominator time, seconds.
        :param tc: Bounded second lead-lag numerator time, seconds.
        :param vamax: Second-stage upper output capability.
        :param vamin: Second-stage lower output capability.
        :param vrmax: Upper field-forcing capability at unit terminal voltage.
        :param vrmin: Lower field-forcing capability at unit terminal voltage.
        :param te: Positive rotating-field time, seconds.
        :param vfelim: Field-current feedback threshold.
        :param kh: Nonnegative field-current feedback gain.
        :param vhmax: Nonnegative feedback input ceiling.
        :param th: Feedback denominator time, seconds.
        :param tj: Feedback numerator time, seconds.
        :param kc: Nonnegative diode commutation coefficient.
        :param kd: Nonnegative generator-current demagnetization coefficient.
        :param ke: Positive rotating-field resistance coefficient.
        :param e1: First saturation voltage sample.
        :param se1: First saturation factor.
        :param e2: Second saturation voltage sample.
        :param se2: Second saturation factor.
        :param vfemax: Positive field-current-equivalent ceiling.
        :param vemin: Nonnegative internal field-voltage floor.
        :param minimum_location: Minimum-excitation signal insertion.
        :param maximum_location: Maximum-excitation signal insertion.
        :param limit_voltage: Fixed or terminal-dependent forcing capability.
        """
        self.tr: float = tr
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
        self.vfelim: float = vfelim
        self.kh: float = kh
        self.vhmax: float = vhmax
        self.th: float = th
        self.tj: float = tj
        self.kc: float = kc
        self.kd: float = kd
        self.ke: float = ke
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.vfemax: float = vfemax
        self.vemin: float = vemin
        self.minimum_location: Ac6cLimiterLocation = minimum_location
        self.maximum_location: Ac6cLimiterLocation = maximum_location
        self.limit_voltage: FieldLimitVoltage = limit_voltage


def build_ac6c_template(vf: VarFactory, name: str | None = None,
                        parameters: Ac6cParameters | None = None) -> RmsModelTemplate:
    """Build a brushless controller with two lead-lags and input-limited field feedback.

    Sensed voltage opposes reference, supplementary signal and signed limiter
    additions. The first lead-lag is unbounded; the second tracks its bounded
    output. Minimum high and maximum low gates follow that bounded stage.
    Feedback senses winding-current equivalent above its threshold, clips to a
    nonnegative ceiling, then passes through a lead-lag. It subtracts after both
    gates, before fixed or terminal-dependent forcing limits. Five positive-time
    states store sensing, both lead-lags, feedback and internal field voltage.
    Zero-time stages reduce algebraically; improper lead/zero-lag pairs reject.

    Internal field voltage yields delivered field through a loaded diode bridge.
    Initial field voltage inverts that bridge, then winding loss and the clipped
    feedback determine required regulator demand and reference. The winding
    observes directional lower-voltage and upper-current stops. Inputs are
    sensed voltage, reference, supplement, generator field current, terminal
    magnitude, minimum and maximum limiter; outputs are delivered field and the
    two pre-gate demands. Signals use compatible per-unit bases, times seconds.

    :param vf: Shared symbolic variable factory.
    :param name: Optional unique instance label.
    :param parameters: Physical settings and limiter locations.
    :return: Native rotating-field excitation controller.
    :raises ValueError: Invalid physical domain or improper structural transfer.
    """
    p: Ac6cParameters = Ac6cParameters() if parameters is None else parameters
    values: tuple[float,...] = (p.tr,p.ka,p.ta,p.tk,p.tb,p.tc,p.vamax,p.vamin,p.vrmax,p.vrmin,p.te,
        p.vfelim,p.kh,p.vhmax,p.th,p.tj,p.kc,p.kd,p.ke,p.e1,p.se1,p.e2,p.se2,p.vfemax,p.vemin)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Brushless coefficients must be finite')
    elif min(p.tr,p.ta,p.tk,p.tb,p.tc,p.kh,p.vhmax,p.th,p.tj,p.kc,p.kd,p.vemin,p.e1,p.se1,p.e2,p.se2) < 0 or min(p.ka,p.te,p.ke,p.vfemax) <= 0:
        raise ValueError('Brushless gains, times or field capabilities are invalid')
    elif (p.ta == 0 and p.tk != 0) or (p.tb == 0 and p.tc != 0) or (p.th == 0 and p.tj != 0 and p.kh > 0):
        raise ValueError('A positive lead cannot have a zero denominator time')
    elif p.vamax <= p.vamin or p.vrmax <= p.vrmin:
        raise ValueError('Brushless regulator capabilities must be ordered')
    elif (p.se1 == 0) != (p.se2 == 0):
        raise ValueError('Magnetic saturation requires two samples or two zeros')
    elif p.se1 > 0 and (p.e1 == p.e2 or (p.e2-p.e1)*(p.e2*p.se2-p.e1*p.se1) <= 0):
        raise ValueError('Magnetic saturation samples must be monotone')
    elif not isinstance(p.minimum_location,Ac6cLimiterLocation) or not isinstance(p.maximum_location,Ac6cLimiterLocation) or not isinstance(p.limit_voltage,FieldLimitVoltage):
        raise ValueError('Brushless limiter selection is invalid')
    else:
        pass
    c: ControlRealization = ControlRealization(vf,'AC6C' if name is None else name)
    tr: Var = c.parameter('TR',p.tr)
    ka: Var = c.parameter('KA',p.ka)
    ta: Var = c.parameter('TA',p.ta)
    tk: Var = c.parameter('TK',p.tk)
    tb: Var = c.parameter('TB',p.tb)
    tc: Var = c.parameter('TC',p.tc)
    vamax: Var = c.parameter('VAMAX',p.vamax)
    vamin: Var = c.parameter('VAMIN',p.vamin)
    vrmax: Var = c.parameter('VRMAX',p.vrmax)
    vrmin: Var = c.parameter('VRMIN',p.vrmin)
    te: Var = c.parameter('TE',p.te)
    vfelim: Var = c.parameter('VFELIM',p.vfelim)
    kh: Var = c.parameter('KH',p.kh)
    vhmax: Var = c.parameter('VHMAX',p.vhmax)
    th: Var = c.parameter('TH',p.th)
    tj: Var = c.parameter('TJ',p.tj)
    kc: Var = c.parameter('KC',p.kc)
    kd: Var = c.parameter('KD',p.kd)
    ke: Var = c.parameter('KE',p.ke)
    vfemax: Var = c.parameter('VFEMAX',p.vfemax)
    vemin: Var = c.parameter('VEMIN',p.vemin)
    field0: Var = c.parameter('Efd0Pu',1.)
    current0: Var = c.parameter('Ifd0Pu',1.)
    voltage0: Var = c.parameter('Us0Pu',1.)
    terminal0: Var = c.parameter('Vt0Pu',1.)
    supplement0: Var = c.parameter('Vs0Pu',0.)
    minimum0: Var = c.parameter('Uel0Pu',0.)
    maximum0: Var = c.parameter('Oel0Pu',0.)
    sensed: Var = c.input('UsPu',voltage0)
    reference: Var = c.input('UsRefPu',voltage0)
    supplement: Var = c.input('VsPu',supplement0)
    current: Var = c.input('IfdPu',current0)
    terminal: Var = c.input('VtPu',terminal0)
    minimum: Var = c.input('UelPu',minimum0)
    maximum: Var = c.input('OelPu',maximum0)
    internal0: Expr = initial_internal_exciter_voltage(field0,kc*current0)
    internal: Var = vf.add_var('InternalVoltagePu_'+c.name)
    loss: Expr
    loss0: Expr
    if p.se1 == 0 and p.se2 == 0:
        loss = Const(0.)
        loss0 = Const(0.)
    else:
        e1: Var = c.parameter('E1',p.e1)
        se1: Var = c.parameter('SE1',p.se1)
        e2: Var = c.parameter('E2',p.e2)
        se2: Var = c.parameter('SE2',p.se2)
        threshold: Expr
        coefficient: Expr
        threshold,coefficient = _quadratic_saturation_coefficients(e1,se1,e2,se2)
        loss = coefficient*sym.max(internal-threshold,Const(0.))**2
        loss0 = coefficient*sym.max(internal0-threshold,Const(0.))**2
    equivalent0: Expr = ke*internal0+loss0+kd*current0
    equivalent: Var = c.algebraic('CurrentEquivalentPu',ke*internal+loss+kd*current,equivalent0)
    field: Var = c.algebraic('EfdPu',internal*_esst3a_fex(sym.safe_divide(kc*current,internal,1.)),field0)
    feedback_input0: Expr = sym.hard_sat(kh*(equivalent0-vfelim),Const(0.),vhmax)
    feedback_input: Var = c.algebraic('FeedbackInputPu',sym.hard_sat(kh*(equivalent-vfelim),Const(0.),vhmax),feedback_input0)
    feedback: Expr = c.lead_lag('FeedbackPu',feedback_input,tj,th,p.tj,p.th,feedback_input0) if p.kh > 0 and p.vhmax > 0 else Const(0.)
    demand0: Expr = equivalent0+feedback_input0
    error0: Expr = demand0/ka
    c.block.init_eqs[reference] = voltage0+error0-supplement0-(minimum0 if p.minimum_location == Ac6cLimiterLocation.ERROR_SUM else Const(0.))+(maximum0 if p.maximum_location == Ac6cLimiterLocation.ERROR_SUM else Const(0.))
    c.block.init_eqs[minimum] = demand0 if p.minimum_location == Ac6cLimiterLocation.REGULATOR_GATE else minimum0
    c.block.init_eqs[maximum] = demand0 if p.maximum_location == Ac6cLimiterLocation.REGULATOR_GATE else maximum0
    measured: Var = c.lag('MeasuredPu',sensed,tr,p.tr,voltage0)
    error: Expr = reference-measured+supplement+(minimum if p.minimum_location == Ac6cLimiterLocation.ERROR_SUM else Const(0.))-(maximum if p.maximum_location == Ac6cLimiterLocation.ERROR_SUM else Const(0.))
    first: Var = c.lead_lag('FirstRegulatorPu',ka*error,tk,ta,p.tk,p.ta,demand0)
    bounded: Var = c.bounded_lead_lag('BoundedRegulatorPu',first,tc,tb,p.tc,p.tb,demand0,vamin,vamax)
    pre_minimum: Var = c.algebraic('PreMinimumPu',bounded,demand0)
    selected: Expr = sym.max(pre_minimum,minimum) if p.minimum_location == Ac6cLimiterLocation.REGULATOR_GATE else pre_minimum
    pre_maximum: Var = c.algebraic('PreMaximumPu',selected,demand0)
    selected = sym.min(pre_maximum,maximum) if p.maximum_location == Ac6cLimiterLocation.REGULATOR_GATE else pre_maximum
    capability: Expr = terminal if p.limit_voltage == FieldLimitVoltage.TERMINAL else Const(1.)
    forcing: Var = c.algebraic('FieldForcingPu',sym.hard_sat(selected-feedback,vrmin*capability,vrmax*capability),equivalent0)
    winding_upper: Expr = (vfemax-kd*current-loss)/ke
    c.differential(internal,(forcing-equivalent)/te,internal0,vemin,winding_upper)
    return c.finish((field,pre_minimum,pre_maximum),'Two-stage rotating-field excitation with bounded feedback and diode output')
