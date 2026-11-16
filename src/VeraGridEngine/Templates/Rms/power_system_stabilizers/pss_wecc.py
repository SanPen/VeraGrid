# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed template for the CGMES PssWECC stabilizer."""

import math
from enum import Enum

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


def build_pss_w_e_c_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        k1: float = 0.0,
        t1: float = 0.0,
        k2: float = 0.0,
        t2: float = 0.0,
        t3: float = 0.0,
        t4: float = 0.0,
        t5: float = 0.0,
        t6: float = 0.0,
        t7: float = 0.0,
        t8: float = 0.0,
        t9: float = 0.0,
        t10: float = 0.0,
        vsmax: float = 0.1,
        vsmin: float = -0.1,
        vcu: float = 0.1,
        vcl: float = -0.1,
        input_signal1_type: Enum | None = None,
        input_signal2_type: Enum | None = None,
) -> RmsModelTemplate:
    """Build the WECC dual-input PSS and its terminal-voltage output gate.

    :param vfactory: Factory that allocates equation variables.
    :param name: Optional unique runtime model name.
    :param k1: First input signal gain.
    :param t1: First input transducer time constant.
    :param k2: Second input signal gain.
    :param t2: Second input transducer time constant.
    :param t3: Washout numerator time constant.
    :param t4: Washout denominator time constant.
    :param t5: First lead time constant.
    :param t6: First lag time constant.
    :param t7: Second lead time constant.
    :param t8: Second lag time constant.
    :param t9: Third lead time constant.
    :param t10: Third lag time constant.
    :param vsmax: Upper stabilizer signal limit.
    :param vsmin: Lower stabilizer signal limit.
    :param vcu: Upper terminal-voltage gate threshold above its operating point.
    :param vcl: Lower terminal-voltage gate threshold below its operating point.
    :param input_signal1_type: Canonical selector for the first measured input.
    :param input_signal2_type: Canonical selector for the second measured input.
    :return: Equation-backed dual-input stabilizer with voltage-gate ports.
    """
    values: tuple[float, ...] = (
        k1, t1, k2, t2, t3, t4, t5, t6, t7, t8, t9, t10,
        vsmax, vsmin, vcu, vcl,
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError('PssWECC parameters must be finite')
    elif min(t1, t2, t3, t4, t5, t6, t7, t8, t9, t10) < 0.0:
        raise ValueError('PssWECC filter times must be nonnegative')
    elif vsmin >= vsmax or vcl >= vcu:
        raise ValueError('PssWECC limiter bounds must be ordered')
    elif t4 == 0.0 and t3 != 0.0:
        raise ValueError('PssWECC washout denominator T4 must be positive when T3 is nonzero')
    else:
        pass

    template_name: str = 'PssWECC' if name is None else name
    model: ControlRealization = ControlRealization(vfactory, template_name)
    signal1: Var = model.input('Signal1Pu', Const(0.0))
    signal2: Var = model.input('Signal2Pu', Const(0.0))
    terminal_voltage: Var = model.input('TerminalVoltagePu', Const(1.0))
    voltage_reference: Var = model.input('VoltageReferencePu', Const(1.0))
    transducer1: Var = model.lag(
        'Signal1TransducerPu', signal1,
        model.parameter('PssWECC.t1', t1), t1, signal1,
    )
    transducer2: Var = model.lag(
        'Signal2TransducerPu', signal2,
        model.parameter('PssWECC.t2', t2), t2, signal2,
    )
    input_sum: Expr = (
        model.parameter('PssWECC.k1', k1) * transducer1
        + model.parameter('PssWECC.k2', k2) * transducer2
    )
    washout_numerator_time: Var = model.parameter('PssWECC.t3', t3)
    washout_denominator_time: Var = model.parameter('PssWECC.t4', t4)
    if t3 == 0.0:
        washout: Expr = Const(0.0)
    else:
        washout_memory: Var = model.lag(
            'WashoutMemoryPu', input_sum,
            washout_denominator_time, t4, input_sum,
        )
        washout = model.algebraic(
            'WashoutPu',
            washout_numerator_time / washout_denominator_time
            * (input_sum - washout_memory),
            Const(0.0),
        )
    phase1: Var = model.lead_lag(
        'Phase1Pu', washout,
        model.parameter('PssWECC.t5', t5), model.parameter('PssWECC.t6', t6),
        t5, t6, Const(0.0),
    )
    phase2: Var = model.lead_lag(
        'Phase2Pu', phase1,
        model.parameter('PssWECC.t7', t7), model.parameter('PssWECC.t8', t8),
        t7, t8, Const(0.0),
    )
    phase3: Var = model.lead_lag(
        'Phase3Pu', phase2,
        model.parameter('PssWECC.t9', t9), model.parameter('PssWECC.t10', t10),
        t9, t10, Const(0.0),
    )
    limited_signal: Expr = sym.hard_sat(
        phase3,
        model.parameter('PssWECC.vsmin', vsmin),
        model.parameter('PssWECC.vsmax', vsmax),
    )
    voltage_gate: Expr = (
        sym.heaviside(terminal_voltage - voltage_reference - model.parameter('PssWECC.vcl', vcl))
        * sym.heaviside(voltage_reference + model.parameter('PssWECC.vcu', vcu) - terminal_voltage)
    )
    output: Var = model.algebraic('VsPu', limited_signal * voltage_gate, Const(0.0))
    template: RmsModelTemplate = model.finish((output,), 'CGMES PssWECC dual-input stabilizer')
    template.comment = (
        'CGMES PssWECC EA1329 signal filters, washout, phase compensation, limiter, '
        'terminal-voltage gate, and canonical input selectors.'
    )
    parameter_values: tuple[tuple[str, object], ...] = (
        ('enabled', None),
        ('inputSignal1Type', input_signal1_type),
        ('inputSignal2Type', input_signal2_type),
    )
    for parameter_name, parameter_value in parameter_values:
        parameter_variable: Var = vfactory.add_var(f'PssWECC.{parameter_name}_{template_name}')
        template.block.event_dict[parameter_variable] = vfactory.add_const(value=parameter_value)
    return template
