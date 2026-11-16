# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcBBC transformer-fed static excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcBBCParameters:
    """Numeric settings and switch declared by the canonical CGMES ExcBBC class."""

    __slots__ = ('t1', 't2', 't3', 't4', 'k', 'vrmin', 'vrmax', 'efdmin', 'efdmax', 'xe', 'switch')

    def __init__(
            self,
            t1: float = 6.0,
            t2: float = 1.0,
            t3: float = 0.05,
            t4: float = 0.01,
            k: float = 300.0,
            vrmin: float = -5.0,
            vrmax: float = 5.0,
            efdmin: float = -5.0,
            efdmax: float = 5.0,
            xe: float = 0.05,
            switch: bool = True,
    ) -> None:
        """Store the parameters used by the EA diagram realization.

        :param t1: Regulator numerator time constant in seconds.
        :param t2: Regulator feedback time constant in seconds.
        :param t3: Voltage-error lead time constant in seconds.
        :param t4: Voltage-error lag time constant in seconds.
        :param k: Regulator gain.
        :param vrmin: Regulator lower output bound.
        :param vrmax: Regulator upper output bound.
        :param efdmin: Open-circuit field-voltage lower bound.
        :param efdmax: Open-circuit field-voltage upper bound.
        :param xe: Excitation-system output reactance.
        :param switch: Selects Vs at field output when true, voltage error otherwise.
        """
        self.t1: float = t1
        self.t2: float = t2
        self.t3: float = t3
        self.t4: float = t4
        self.k: float = k
        self.vrmin: float = vrmin
        self.vrmax: float = vrmax
        self.efdmin: float = efdmin
        self.efdmax: float = efdmax
        self.xe: float = xe
        self.switch: bool = switch


def build_exc_b_b_c_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcBBCParameters | None = None,
) -> RmsModelTemplate:
    """Build ExcBBC from its local EA block diagram.

    :param vfactory: Factory owning the symbolic model graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed model with voltage, reference, Vs, Ifd, and Efd ports.
    :raises ValueError: Invalid times, bounds, reactance, or nonfinite settings.
    """
    settings: ExcBBCParameters = ExcBBCParameters() if parameters is None else parameters
    template_name: str = 'ExcBBC' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.t1, settings.t2, settings.t3, settings.t4, settings.k,
        settings.vrmin, settings.vrmax, settings.efdmin, settings.efdmax, settings.xe,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcBBC parameters must be finite')
    elif settings.t1 <= 0.0 or settings.t2 <= 0.0 or settings.t3 < 0.0 or settings.t4 < 0.0:
        raise ValueError('ExcBBC requires positive T1/T2 and nonnegative T3/T4')
    elif settings.vrmin >= settings.vrmax or settings.efdmin >= settings.efdmax:
        raise ValueError('ExcBBC regulator and field limits must be ordered')
    elif settings.xe < 0.0:
        raise ValueError('ExcBBC XE must be nonnegative')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    t1: Var = builder.parameter('T1', settings.t1)
    t2: Var = builder.parameter('T2', settings.t2)
    t3: Var = builder.parameter('T3', settings.t3)
    t4: Var = builder.parameter('T4', settings.t4)
    gain: Var = builder.parameter('K', settings.k)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    efdmin: Var = builder.parameter('EFDMIN', settings.efdmin)
    efdmax: Var = builder.parameter('EFDMAX', settings.efdmax)
    xe: Var = builder.parameter('XE', settings.xe)
    builder.parameter('SWITCH', 1.0 if settings.switch else 0.0)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    field_current: Var = builder.input('IfdPu', Const(1.0))

    voltage_error: Expr = reference - terminal_voltage
    if settings.switch:
        prefilter_input: Expr = voltage_error
    else:
        prefilter_input = voltage_error + supplementary
    if settings.t4 == 0.0:
        compensated_error: Expr = prefilter_input
    else:
        compensated_error = builder.lead_lag(
            'VoltageCompensatorPu', prefilter_input, t3, t4, settings.t3, settings.t4,
            prefilter_input,
        )

    # Feedback from the bounded regulator output realizes K(1+sT2)/(1+sT1).
    regulator_feedback_state: Var = vfactory.add_var(f'RegulatorFeedbackPu_{template_name}')
    feedback_gain: Expr = t1 / t2 - Const(1.0)
    regulator_demand: Expr = (t2 / t1) * (gain * compensated_error + feedback_gain * regulator_feedback_state)
    regulator_output: Var = builder.algebraic(
        'RegulatorOutputPu', sym.hard_sat(regulator_demand, vrmin, vrmax),
        sym.hard_sat(gain * prefilter_input, vrmin, vrmax),
    )
    builder.differential(
        regulator_feedback_state,
        (regulator_output - regulator_feedback_state) / t2,
        regulator_output,
    )
    field_signal: Expr = regulator_output
    if settings.switch:
        field_signal = field_signal + supplementary
    else:
        pass
    field_voltage: Var = builder.algebraic(
        'EfdPu',
        sym.hard_sat(
            field_signal - xe * field_current,
            terminal_voltage * efdmin,
            terminal_voltage * efdmax,
        ),
        Const(1.0),
    )
    return builder.finish((field_voltage,), 'CGMES ExcBBC transformer-fed static exciter')
