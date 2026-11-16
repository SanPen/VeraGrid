# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# SPDX-License-Identifier: MPL-2.0
"""AC6A and ESAC6A brushless excitation with distinct lead-lag limiting."""
from __future__ import annotations

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Templates.Rms.synchronous_machines.genrou_exc_gov_rms_template import _esst3a_fex
from VeraGridEngine.Templates.Rms.excitation_systems.ieeex1_ieeest_rms_template import _quadratic_saturation_coefficients
from VeraGridEngine.Templates.Rms.excitation_systems.ac8b import initial_internal_exciter_voltage
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class Ac6aParameters:
    """Source-independent physical coefficients shared by AC6A variants."""

    __slots__ = ('tr', 'ka', 'ta', 'tk', 'tb', 'tc', 'vamax', 'vamin', 'vrmax',
                 'vrmin', 'te', 'vfelim', 'kh', 'vhmax', 'th', 'tj', 'kc',
                 'kd', 'ke', 'e1', 'se1', 'e2', 'se2')

    def __init__(self, tr: float = 0.02, ka: float = 20.0, ta: float = 0.05,
                 tk: float = 0.02, tb: float = 0.05, tc: float = 0.02,
                 vamax: float = 5.0, vamin: float = -5.0, vrmax: float = 5.0,
                 vrmin: float = -5.0, te: float = 0.5, vfelim: float = 2.0,
                 kh: float = 0.2, vhmax: float = 2.0, th: float = 0.1,
                 tj: float = 0.05, kc: float = 0.1, kd: float = 0.1,
                 ke: float = 1.0, e1: float = 3.0, se1: float = 0.1,
                 e2: float = 4.0, se2: float = 0.3) -> None:
        """Store the 23 PSS/E CON values in named physical fields.

        :param tr: Terminal-voltage transducer time, seconds.
        :param ka: Regulator gain.
        :param ta: First regulator lag time, seconds.
        :param tk: First regulator lead time, seconds.
        :param tb: Bounded regulator lag time, seconds.
        :param tc: Bounded regulator lead time, seconds.
        :param vamax: Upper bounded-regulator output.
        :param vamin: Lower bounded-regulator output.
        :param vrmax: Upper terminal-scaled forcing limit.
        :param vrmin: Lower terminal-scaled forcing limit.
        :param te: Exciter field time, seconds.
        :param vfelim: Field-current feedback threshold.
        :param kh: Field-current feedback gain.
        :param vhmax: Feedback signal upper limit.
        :param th: Feedback lead-lag lag time, seconds.
        :param tj: Feedback lead-lag lead time, seconds.
        :param kc: Rectifier commutation coefficient.
        :param kd: Exciter demagnetizing coefficient.
        :param ke: Exciter field resistance coefficient.
        :param e1: First saturation voltage sample.
        :param se1: Saturation factor at ``e1``.
        :param e2: Second saturation voltage sample.
        :param se2: Saturation factor at ``e2``.
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


def build_ac6a_template(vf: VarFactory, name: str | None = None,
                        parameters: Ac6aParameters | None = None) -> RmsModelTemplate:
    """Build revised AC6A with output-tracking non-windup on its second stage.

    :param vf: Shared symbolic variable factory.
    :param name: Optional unique instance label.
    :param parameters: Physical coefficients in PSS/E CON order.
    :return: Five-state brushless exciter with source-compatible ports.
    :raises ValueError: Invalid coefficients or infeasible initial operating point.
    """
    return _build_ac6a_family(vf, name, parameters, True)


def build_esac6a_template(vf: VarFactory, name: str | None = None,
                          parameters: Ac6aParameters | None = None) -> RmsModelTemplate:
    """Build original ESAC6A with the pre-2005 downstream output limiter.

    :param vf: Shared symbolic variable factory.
    :param name: Optional unique instance label.
    :param parameters: Physical coefficients in PSS/E CON order.
    :return: Five-state brushless exciter with source-compatible ports.
    :raises ValueError: Invalid coefficients or infeasible initial operating point.
    """
    return _build_ac6a_family(vf, name, parameters, False)


def _build_ac6a_family(vf: VarFactory, name: str | None,
                       parameters: Ac6aParameters | None,
                       revised_non_windup: bool) -> RmsModelTemplate:
    """Assemble the common AC6A physical chain and selected limiter memory law.

    :param vf: Shared symbolic variable factory.
    :param name: Optional unique instance label.
    :param parameters: Physical coefficients in source order.
    :param revised_non_windup: Select the IEEE 421.5-2005 output-tracking rule.
    :return: Native brushless exciter template.
    :raises ValueError: Invalid source-domain coefficients or infeasible limits.
    """
    p: Ac6aParameters = Ac6aParameters() if parameters is None else parameters
    values: tuple[float, ...] = (p.tr, p.ka, p.ta, p.tk, p.tb, p.tc, p.vamax,
        p.vamin, p.vrmax, p.vrmin, p.te, p.vfelim, p.kh, p.vhmax, p.th, p.tj,
        p.kc, p.kd, p.ke, p.e1, p.se1, p.e2, p.se2)
    if not all(math.isfinite(value) for value in values):
        raise ValueError('AC6A coefficients must be finite')
    elif min(p.tr, p.ta, p.tk, p.tb, p.tc, p.kh, p.vhmax, p.th, p.tj,
             p.kc, p.kd, p.e1, p.se1, p.e2, p.se2) < 0 or min(p.ka, p.te, p.ke) <= 0:
        raise ValueError('AC6A gains, times or saturation coefficients are invalid')
    elif (p.ta == 0 and p.tk != 0) or (p.tb == 0 and p.tc != 0) or (p.th == 0 and p.tj != 0 and p.kh > 0):
        raise ValueError('AC6A positive lead requires a positive lag')
    elif p.vamax <= p.vamin or p.vrmax <= p.vrmin:
        raise ValueError('AC6A regulator limits must be ordered')
    elif (p.se1 == 0) != (p.se2 == 0):
        raise ValueError('AC6A saturation requires two samples or two zero factors')
    elif p.se1 > 0 and (p.e1 == p.e2 or (p.e2 - p.e1) * (p.e2 * p.se2 - p.e1 * p.se1) <= 0):
        raise ValueError('AC6A saturation samples must define a monotone fit')
    else:
        pass

    label: str = ('AC6A' if revised_non_windup else 'ESAC6A') if name is None else name
    c: ControlRealization = ControlRealization(vf, label)
    tr: Var = c.parameter('TR', p.tr)
    ka: Var = c.parameter('KA', p.ka)
    ta: Var = c.parameter('TA', p.ta)
    tk: Var = c.parameter('TK', p.tk)
    tb: Var = c.parameter('TB', p.tb)
    tc: Var = c.parameter('TC', p.tc)
    vamax: Var = c.parameter('VAMAX', p.vamax)
    vamin: Var = c.parameter('VAMIN', p.vamin)
    vrmax: Var = c.parameter('VRMAX', p.vrmax)
    vrmin: Var = c.parameter('VRMIN', p.vrmin)
    te: Var = c.parameter('TE', p.te)
    vfelim: Var = c.parameter('VFELIM', p.vfelim)
    kh: Var = c.parameter('KH', p.kh)
    vhmax: Var = c.parameter('VHMAX', p.vhmax)
    th: Var = c.parameter('TH', p.th)
    tj: Var = c.parameter('TJ', p.tj)
    kc: Var = c.parameter('KC', p.kc)
    kd: Var = c.parameter('KD', p.kd)
    ke: Var = c.parameter('KE', p.ke)
    field0: Var = c.parameter('Efd0Pu', 1.0)
    current0: Var = c.parameter('Ifd0Pu', 1.0)
    voltage0: Var = c.parameter('Vt0Pu', 1.0)
    supplement0: Var = c.parameter('Vs0Pu', 0.0)
    uel0: Var = c.parameter('Uel0Pu', 0.0)
    measured: Var = c.input('VtPu', voltage0)
    reference: Var = c.input('VrefPu', voltage0)
    supplement: Var = c.input('VsPu', supplement0)
    uel: Var = c.input('UelPu', uel0)
    current: Var = c.input('IfdPu', current0)
    terminal: Var = c.input('VtLimitPu', voltage0)

    internal0: Expr = initial_internal_exciter_voltage(field0, kc * current0)
    internal: Var = vf.add_var('InternalVoltagePu_' + label)
    if p.se1 == 0 and p.se2 == 0:
        loss: Expr = Const(0.0)
        loss0: Expr = Const(0.0)
    else:
        e1: Var = c.parameter('E1', p.e1)
        se1: Var = c.parameter('SE1', p.se1)
        e2: Var = c.parameter('E2', p.e2)
        se2: Var = c.parameter('SE2', p.se2)
        threshold: Expr
        coefficient: Expr
        threshold, coefficient = _quadratic_saturation_coefficients(e1, se1, e2, se2)
        loss = coefficient * sym.max(internal - threshold, Const(0.0)) ** 2
        loss0 = coefficient * sym.max(internal0 - threshold, Const(0.0)) ** 2

    equivalent0: Expr = ke * internal0 + loss0 + kd * current0
    equivalent: Var = c.algebraic('CurrentEquivalentPu', ke * internal + loss + kd * current, equivalent0)
    field: Var = c.algebraic('EfdPu', internal * _esst3a_fex(sym.safe_divide(kc * current, internal, 1.0)), field0)
    feedback_input0: Expr = sym.hard_sat(kh * (equivalent0 - vfelim), Const(0.0), vhmax)
    feedback_input: Var = c.algebraic('FeedbackInputPu', sym.hard_sat(kh * (equivalent - vfelim), Const(0.0), vhmax), feedback_input0)
    feedback: Expr = c.lead_lag('FeedbackPu', feedback_input, tj, th, p.tj, p.th, feedback_input0) if p.kh > 0 and p.vhmax > 0 else Const(0.0)
    measured_filter: Var = c.lag('MeasuredVoltagePu', measured, tr, p.tr, voltage0)
    error: Expr = reference - measured_filter + supplement + uel
    first0: Expr = equivalent0 + feedback_input0
    first: Var = c.lead_lag('FirstRegulatorPu', ka * error, tk, ta, p.tk, p.ta, first0)
    bounded_input: Expr = first
    if revised_non_windup:
        regulator: Var = c.bounded_lead_lag('BoundedRegulatorPu', bounded_input, tc, tb,
            p.tc, p.tb, equivalent0, vamin, vamax)
    else:
        unrestricted: Var = c.lead_lag('UnboundedRegulatorPu', bounded_input, tc, tb,
            p.tc, p.tb, equivalent0)
        regulator = c.algebraic('BoundedRegulatorPu', sym.hard_sat(unrestricted, vamin, vamax), equivalent0)
    forcing: Var = c.algebraic('FieldForcingPu', sym.hard_sat(regulator - feedback, vrmin * terminal, vrmax * terminal), equivalent0)
    c.block.init_eqs[reference] = voltage0 + first0 / ka - supplement0 - uel0
    c.block.init_eqs[terminal] = voltage0
    c.differential(internal, (forcing - equivalent) / te, internal0)
    return c.finish((field, regulator, forcing), 'IEEE AC6A brushless excitation with source-specific non-windup')
