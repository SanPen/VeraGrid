# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""CGMES ExcAC5A alternator-supplied rectifier excitation system."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcAC5AParameters:
    """CGMES ExcAC5A regulator, washout feedback, exciter, and rectifier settings."""

    __slots__ = (
        'ka', 'ks', 'tb', 'tc', 'ta', 'vrmax', 'vrmin', 'ke', 'te', 'kf',
        'tf1', 'tf2', 'tf3', 'efd1', 'seefd1', 'efd2', 'seefd2', 'a',
    )

    def __init__(
            self,
            ka: float = 400.0,
            ks: float = 0.0,
            tb: float = 0.0,
            tc: float = 0.0,
            ta: float = 0.02,
            vrmax: float = 7.3,
            vrmin: float = -7.3,
            ke: float = 1.0,
            te: float = 0.8,
            kf: float = 0.03,
            tf1: float = 1.0,
            tf2: float = 0.8,
            tf3: float = 0.0,
            efd1: float = 5.6,
            seefd1: float = 0.86,
            efd2: float = 4.2,
            seefd2: float = 0.5,
            a: float = 1.0,
    ) -> None:
        """Store canonical AC5A parameters.

        :param ka: Voltage regulator gain.
        :param ks: Generator speed multiplication selector.
        :param tb: Lead-lag denominator time in seconds.
        :param tc: Lead-lag numerator time in seconds.
        :param ta: Amplifier time in seconds.
        :param vrmax: Regulator output upper limit.
        :param vrmin: Regulator output lower limit.
        :param ke: Exciter field constant.
        :param te: Exciter time in seconds.
        :param kf: Stabilizing feedback gain.
        :param tf1: First feedback filter time in seconds.
        :param tf2: Second feedback filter time in seconds.
        :param tf3: Feedback zero time in seconds.
        :param efd1: First saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        :param a: Exciter denominator coefficient.
        """
        self.ka: float = ka
        self.ks: float = ks
        self.tb: float = tb
        self.tc: float = tc
        self.ta: float = ta
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ke: float = ke
        self.te: float = te
        self.kf: float = kf
        self.tf1: float = tf1
        self.tf2: float = tf2
        self.tf3: float = tf3
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2
        self.a: float = a


def build_exc_a_c5_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcAC5AParameters | None = None,
) -> RmsModelTemplate:
    """Build AC5A regulator, washout feedback, field, and rectifier equations.

    The two feedback poles are realized as serial states and the rational
    feedback output is formed from their states without differentiating a port.

    :param vfactory: Factory that owns the symbolic model.
    :param name: Optional runtime instance name.
    :param parameters: Parsed CGMES values.
    :return: Equation-backed AC5A with terminal voltage and Efd ports.
    :raises ValueError: Invalid times, limits, or saturation points.
    """
    settings: ExcAC5AParameters = ExcAC5AParameters() if parameters is None else parameters
    template_name: str = 'ExcAC5A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ks, settings.tb, settings.tc, settings.ta,
        settings.vrmax, settings.vrmin, settings.ke, settings.te, settings.kf,
        settings.tf1, settings.tf2, settings.tf3, settings.efd1, settings.seefd1,
        settings.efd2, settings.seefd2, settings.a,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcAC5A parameters must be finite')
    elif min(settings.tb, settings.tc, settings.ta, settings.tf1, settings.tf2, settings.tf3) < 0.0:
        raise ValueError('ExcAC5A times must be nonnegative')
    elif settings.tf1 <= 0.0 or settings.tf2 <= 0.0 or settings.te <= 0.0:
        raise ValueError('ExcAC5A T_E, T_F1, and T_F2 must be positive')
    elif settings.vrmin >= settings.vrmax:
        raise ValueError('ExcAC5A lower regulator limit must be below upper limit')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcAC5A requires zero lead when T_B is zero')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcAC5A saturation points must be distinct and positive')
    elif settings.seefd1 <= 0.0 or settings.seefd2 <= 0.0 or settings.ke <= 0.0:
        raise ValueError('ExcAC5A saturation values and K_E must be positive')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ks: Var = builder.parameter('KS', settings.ks)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    ta: Var = builder.parameter('TA', settings.ta)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    ke: Var = builder.parameter('KE', settings.ke)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
    tf1: Var = builder.parameter('TF1', settings.tf1)
    tf2: Var = builder.parameter('TF2', settings.tf2)
    tf3: Var = builder.parameter('TF3', settings.tf3)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    exciter_a: Var = builder.parameter('A', settings.a)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    stabilizer: Var = builder.input('UpssPu', Const(0.0))
    speed: Var | None = None
    if settings.ks != 0.0:
        speed = builder.input('OmegaPu', Const(1.0))
    else:
        pass

    exciter_voltage: Var = vfactory.add_var(f'VePu_{template_name}')
    field_voltage: Var = vfactory.add_var(f'EfdPu_{template_name}')
    regulator_state: Var = vfactory.add_var(f'RegulatorPu_{template_name}')
    saturation_b: float = math.log(settings.seefd2 / settings.seefd1) / (settings.efd2 - settings.efd1)
    saturation_a: float = settings.seefd1 * math.exp(-saturation_b * settings.efd1)
    saturation: Expr = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_voltage)
    first_feedback_state: Var = builder.lag(
        'FeedbackFirstMemoryPu', regulator_state, tf1, settings.tf1, Const(0.0),
    )
    second_feedback_state: Var = builder.lag(
        'FeedbackSecondMemoryPu', first_feedback_state, tf2, settings.tf2, Const(0.0),
    )
    first_feedback_derivative: Expr = (regulator_state - first_feedback_state) / tf1
    second_feedback_derivative: Expr = (
        first_feedback_state - second_feedback_state
    ) / tf2
    second_feedback_second_derivative: Expr = (
        first_feedback_derivative - second_feedback_derivative
    ) / tf2
    feedback_signal: Expr = kf * (
        second_feedback_derivative + tf3 * second_feedback_second_derivative
    )
    voltage_error: Var = builder.algebraic(
        'VoltageErrorPu', reference - terminal_voltage + stabilizer - feedback_signal, Const(0.0),
    )
    lead_lag: Var = builder.lead_lag(
        'LeadLagPu', voltage_error, tc, tb, settings.tc, settings.tb, Const(0.0),
    )
    regulator_output: Var = builder.lag(
        'RegulatorPu', ka * lead_lag, ta, settings.ta, Const(0.0), vrmin, vrmax,
        output=regulator_state,
    )
    exciter_derivative: Expr = (
        regulator_output - (exciter_a + ke + saturation) * exciter_voltage
    ) / te
    builder.differential(exciter_voltage, exciter_derivative, Const(1.0))
    speed_correction: Expr = Const(1.0)
    if speed is not None:
        speed_correction = Const(1.0) + ks * (speed - Const(1.0))
    else:
        pass
    builder.block.algebraic_vars.append(field_voltage)
    builder.block.algebraic_eqs.append(field_voltage - exciter_voltage * speed_correction)
    builder.block.init_eqs[field_voltage] = Const(1.0)
    return builder.finish((field_voltage,), 'CGMES ExcAC5A excitation system')
