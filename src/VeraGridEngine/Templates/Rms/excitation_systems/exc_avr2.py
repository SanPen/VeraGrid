# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcAVR2 excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAVR2Parameters:
    """Numeric settings for the canonical CGMES ExcAVR2 model."""

    __slots__ = ('ka', 'vrmn', 'vrmx', 'ta', 'tb', 'te', 'e1', 'se1', 'e2', 'se2', 'kf', 'tf1', 'tf2')

    def __init__(
            self,
            ka: float = 500.0,
            vrmn: float = -6.0,
            vrmx: float = 7.0,
            ta: float = 0.02,
            tb: float = 0.0,
            te: float = 1.0,
            e1: float = 4.18,
            se1: float = 0.1,
            e2: float = 3.14,
            se2: float = 0.03,
            kf: float = 0.02,
            tf1: float = 1.0,
            tf2: float = 1.0,
    ) -> None:
        """Store parsed settings or local EA typical values.

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
        :param kf: Regulator feedback gain.
        :param tf1: Feedback washout time constant.
        :param tf2: Feedback input lag time constant.
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
        self.tf1: float = tf1
        self.tf2: float = tf2


def build_exc_a_v_r2_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAVR2Parameters | None = None,
) -> RmsModelTemplate:
    """Build AVR2 lead-lag regulation, two-pole washout, saturation, and exciter equations.

    :param vfactory: Factory that owns symbolic variables.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES settings.
    :return: Equation-backed model with voltage, stabilizer, and Efd ports.
    :raises ValueError: Invalid time, limit, or saturation settings.
    """
    settings: ExcAVR2Parameters = ExcAVR2Parameters() if parameters is None else parameters
    template_name: str = 'ExcAVR2' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.vrmn, settings.vrmx, settings.ta, settings.tb,
        settings.te, settings.e1, settings.se1, settings.e2, settings.se2,
        settings.kf, settings.tf1, settings.tf2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAVR2 parameters must be finite')
    elif min(settings.ta, settings.tb, settings.te, settings.tf1, settings.tf2) < 0.0:
        raise ValueError('ExcAVR2 times must be nonnegative')
    elif settings.te <= 0.0 or settings.tf1 <= 0.0 or settings.tf2 <= 0.0:
        raise ValueError('ExcAVR2 TE, TF1, and TF2 must be positive')
    elif settings.ta == 0.0 and settings.tb != 0.0:
        raise ValueError('ExcAVR2 requires zero TB when TA is zero')
    elif settings.vrmn >= settings.vrmx:
        raise ValueError('ExcAVR2 regulator bounds must be ordered')
    elif settings.e1 <= 0.0 or settings.e2 <= 0.0 or settings.e1 == settings.e2:
        raise ValueError('ExcAVR2 saturation points must be distinct and positive')
    elif settings.se1 <= 0.0 or settings.se2 <= 0.0:
        raise ValueError('ExcAVR2 saturation values must be positive')
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
    tf1: Var = builder.parameter('TF1', settings.tf1)
    tf2: Var = builder.parameter('TF2', settings.tf2)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))

    regulator_state: Var = vfactory.add_var(f'RegulatorOutputPu_{template_name}')
    feedback_input: Var = builder.lag(
        'FeedbackInputMemoryPu', regulator_state, tf2, settings.tf2, Const(0.0),
    )
    feedback_washout_memory: Var = builder.lag(
        'FeedbackWashoutMemoryPu', feedback_input, tf1, settings.tf1, Const(0.0),
    )
    washout_output: Expr = kf * (feedback_input - feedback_washout_memory)
    avr_voltage: Expr = ka * (reference - terminal_voltage + stabilizer - washout_output)
    builder.block.algebraic_vars.append(regulator_state)
    if settings.ta == 0.0:
        regulator_output: Expr = sym.hard_sat(avr_voltage, vrmn, vrmx)
    else:
        lead_ratio: Expr = tb / ta
        regulator_memory: Var = builder.lag(
            'RegulatorMemoryPu',
            avr_voltage,
            ta,
            settings.ta,
            Const(0.0),
            vrmn - avr_voltage * lead_ratio,
            vrmx - avr_voltage * lead_ratio,
        )
        regulator_output = (
            lead_ratio * avr_voltage
            + (Const(1.0) - lead_ratio) * regulator_memory
        )
    builder.block.algebraic_eqs.append(regulator_state - regulator_output)
    builder.block.init_eqs[regulator_state] = Const(0.0)
    exciter_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    saturation_slope: float = math.log(settings.se2 / settings.se1) / (settings.e2 - settings.e1)
    saturation_scale: float = settings.se1 * math.exp(-saturation_slope * settings.e1)
    saturation_ratio: Expr = Const(saturation_scale) * sym.exp(Const(saturation_slope) * exciter_voltage)
    saturation_voltage: Expr = saturation_ratio * exciter_voltage
    exciter_derivative: Expr = (regulator_state - saturation_voltage) / te
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0), Const(0.0), Const(1e12))
    return builder.finish((exciter_voltage,), 'CGMES ExcAVR2 excitation system')
