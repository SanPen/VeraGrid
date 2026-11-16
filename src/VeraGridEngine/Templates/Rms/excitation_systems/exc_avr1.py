# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAVR1 excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAVR1Parameters:
    """Numeric settings for the canonical CGMES ExcAVR1 model."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 'ta', 'tb', 'te', 'e1', 'se1', 'e2', 'se2', 'kf', 'tf')

    def __init__(
            self,
            ka: float = 500.0,
            vrmn: float = -6.0,
            vrmx: float = 7.0,
            ta: float = 0.2,
            tb: float = 0.0,
            te: float = 1.0,
            e1: float = 4.18,
            se1: float = 0.1,
            e2: float = 3.14,
            se2: float = 0.03,
            kf: float = 0.02,
            tf: float = 1.0,
    ) -> None:
        """Store parsed parameters or EA typical values.

        :param ka: AVR gain.
        :param vrmn: Lower regulator output limit.
        :param vrmx: Upper regulator output limit.
        :param ta: AVR lag time constant.
        :param tb: AVR lead time constant.
        :param te: Exciter integration time constant.
        :param e1: First saturation voltage point.
        :param se1: Saturation at ``e1``.
        :param e2: Second saturation voltage point.
        :param se2: Saturation at ``e2``.
        :param kf: Rate feedback gain.
        :param tf: Rate feedback lag time constant.
        """
        self.ka: float = ka
        self.vrmn: float = vrmn
        self.vrmx: float = vrmx
        self.ta: float = ta
        self.tb: float = tb
        self.te: float = te
        self.e1: float = e1
        self.se1: float = se1
        self.e2: float = e2
        self.se2: float = se2
        self.kf: float = kf
        self.tf: float = tf


def build_exc_a_v_r1_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAVR1Parameters | None = None,
) -> RmsModelTemplate:
    """Build AVR1 lead-lag, rate feedback, saturation, and exciter equations.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES settings.
    :return: Equation-backed model with voltage and stabilizer inputs and Efd output.
    :raises ValueError: Invalid time, limit, or saturation settings.
    """
    settings: ExcAVR1Parameters = ExcAVR1Parameters() if parameters is None else parameters
    template_name: str = 'ExcAVR1' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.vrmn, settings.vrmx, settings.ta, settings.tb,
        settings.te, settings.e1, settings.se1, settings.e2, settings.se2,
        settings.kf, settings.tf,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAVR1 parameters must be finite')
    elif min(settings.ta, settings.tb, settings.te, settings.tf) < 0.0:
        raise ValueError('ExcAVR1 times must be nonnegative')
    elif settings.te <= 0.0 or settings.tf <= 0.0:
        raise ValueError('ExcAVR1 TE and TF must be positive')
    elif settings.vrmn >= settings.vrmx:
        raise ValueError('ExcAVR1 regulator bounds must be ordered')
    elif settings.ta == 0.0 and settings.tb != 0.0:
        raise ValueError('ExcAVR1 requires zero TB when TA is zero')
    elif settings.e1 <= 0.0 or settings.e2 <= 0.0 or settings.e1 == settings.e2:
        raise ValueError('ExcAVR1 saturation points must be distinct and positive')
    elif settings.se1 <= 0.0 or settings.se2 <= 0.0:
        raise ValueError('ExcAVR1 saturation values must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    vrmn: Var = builder.parameter('VRMN', settings.vrmn)
    vrmx: Var = builder.parameter('VRMX', settings.vrmx)
    ta: Var = builder.parameter('TA', settings.ta)
    tb: Var = builder.parameter('TB', settings.tb)
    te: Var = builder.parameter('TE', settings.te)
    e1: Var = builder.parameter('E1', settings.e1)
    se1: Var = builder.parameter('SE1', settings.se1)
    e2: Var = builder.parameter('E2', settings.e2)
    se2: Var = builder.parameter('SE2', settings.se2)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))

    exciter_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    feedback_memory: Var = builder.lag(
        'FeedbackMemoryPu', exciter_voltage, tf, settings.tf, Const(1.0),
    )
    washout_feedback: Expr = kf * (exciter_voltage - feedback_memory)
    voltage_error: Expr = reference - terminal_voltage + stabilizer - washout_feedback
    regulator_input: Expr = ka * voltage_error
    regulator_output: Var
    if settings.ta == 0.0:
        regulator_output = builder.algebraic(
            'RegulatorOutputPu', sym.hard_sat(regulator_input, vrmn, vrmx), Const(0.0),
        )
    else:
        lead_ratio: Expr = tb / ta
        regulator_memory: Var = builder.lag(
            'RegulatorMemoryPu',
            regulator_input,
            ta,
            settings.ta,
            Const(0.0),
            vrmn - regulator_input * lead_ratio,
            vrmx - regulator_input * lead_ratio,
        )
        regulator_output = builder.algebraic(
            'RegulatorOutputPu',
            lead_ratio * regulator_input + (Const(1.0) - lead_ratio) * regulator_memory,
            Const(0.0),
        )
    saturation_slope: float = math.log(settings.se2 / settings.se1) / (settings.e2 - settings.e1)
    saturation_scale: float = settings.se1 * math.exp(-saturation_slope * settings.e1)
    saturation_ratio: Expr = Const(saturation_scale) * sym.exp(Const(saturation_slope) * exciter_voltage)
    saturation_voltage: Expr = saturation_ratio * exciter_voltage
    exciter_derivative: Expr = (regulator_output - saturation_voltage) / te
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0), Const(0.0), Const(1e12))
    return builder.finish((exciter_voltage,), 'CGMES ExcAVR1 excitation system')
