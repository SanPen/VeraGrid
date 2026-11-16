# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the License was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcDC2A direct-current commutator exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcDC2AParameters:
    """Settings declared by the canonical CGMES ExcDC2A class."""

    __slots__ = (
        'ka', 'ks', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf', 'tf1',
        'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim', 'vtlim',
    )

    def __init__(
            self,
            ka: float = 300.0,
            ks: float = 0.0,
            ta: float = 0.01,
            tb: float = 0.0,
            tc: float = 0.0,
            vrmax: float = 4.95,
            vrmin: float = -4.9,
            ke: float = 1.0,
            te: float = 1.33,
            kf: float = 0.1,
            tf: float = 0.675,
            tf1: float = 0.0,
            efd1: float = 3.05,
            seefd1: float = 0.279,
            efd2: float = 2.29,
            seefd2: float = 0.117,
            exclim: bool = True,
            vtlim: bool = True,
    ) -> None:
        """Store settings using the typical values from the local EA page.

        :param ka: Voltage-regulator gain.
        :param ks: Speed-deviation multiplier coefficient.
        :param ta: Regulator-amplifier time constant.
        :param tb: Lead-lag denominator time constant.
        :param tc: Lead-lag numerator time constant.
        :param vrmax: Regulator upper bound.
        :param vrmin: Regulator lower bound.
        :param ke: Exciter field constant.
        :param te: Exciter integration time constant.
        :param kf: Stabilizing feedback gain.
        :param tf: Stabilizing washout time constant.
        :param tf1: Additional stabilizing feedback lag time constant.
        :param efd1: First saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        :param exclim: Apply a zero lower stop to the exciter integrator.
        :param vtlim: Scale amplifier bounds with terminal voltage.
        """
        self.ka: float = ka
        self.ks: float = ks
        self.ta: float = ta
        self.tb: float = tb
        self.tc: float = tc
        self.vrmax: float = vrmax
        self.vrmin: float = vrmin
        self.ke: float = ke
        self.te: float = te
        self.kf: float = kf
        self.tf: float = tf
        self.tf1: float = tf1
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2
        self.exclim: bool = exclim
        self.vtlim: bool = vtlim


def build_exc_d_c2_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcDC2AParameters | None = None,
) -> RmsModelTemplate:
    """Build DC2A regulator, two-stage washout feedback, and saturated exciter.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed DC2A with voltage, reference, Vs, optional speed, and Efd ports.
    :raises ValueError: Invalid times, bounds, or saturation points.
    """
    settings: ExcDC2AParameters = ExcDC2AParameters() if parameters is None else parameters
    template_name: str = 'ExcDC2A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ks, settings.ta, settings.tb, settings.tc,
        settings.vrmax, settings.vrmin, settings.ke, settings.te, settings.kf,
        settings.tf, settings.tf1, settings.efd1, settings.seefd1, settings.efd2,
        settings.seefd2,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcDC2A parameters must be finite')
    elif min(settings.ta, settings.tb, settings.tc, settings.tf, settings.tf1) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcDC2A times must be nonnegative and TE positive')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcDC2A zero TB requires zero TC')
    elif settings.vrmin >= settings.vrmax:
        raise ValueError('ExcDC2A regulator limits must be ordered')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcDC2A saturation voltages must be distinct and positive')
    elif settings.seefd1 <= 0.0 or settings.seefd2 <= 0.0:
        raise ValueError('ExcDC2A saturation values must be positive')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcDC2A TF must be positive when KF is nonzero')
    else:
        pass

    builder: ControlRealization = ControlRealization(vfactory, template_name)
    ka: Var = builder.parameter('KA', settings.ka)
    ks: Var = builder.parameter('KS', settings.ks)
    ta: Var = builder.parameter('TA', settings.ta)
    tb: Var = builder.parameter('TB', settings.tb)
    tc: Var = builder.parameter('TC', settings.tc)
    vrmax: Var = builder.parameter('VRMAX', settings.vrmax)
    vrmin: Var = builder.parameter('VRMIN', settings.vrmin)
    ke: Var = builder.parameter('KE', settings.ke)
    te: Var = builder.parameter('TE', settings.te)
    kf: Var = builder.parameter('KF', settings.kf)
    tf: Var = builder.parameter('TF', settings.tf)
    tf1: Var = builder.parameter('TF1', settings.tf1)
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    builder.parameter('EXCLIM', 1.0 if settings.exclim else 0.0)
    builder.parameter('VTLIM', 1.0 if settings.vtlim else 0.0)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    voltage_error: Expr = reference - terminal_voltage + supplementary
    exciter_state: Var = vfactory.add_var(f'ExciterVoltagePu_{template_name}')

    if settings.tf1 == 0.0:
        feedback_signal: Expr = exciter_state
    else:
        feedback_signal = builder.lag(
            'FeedbackLagPu', exciter_state, tf1, settings.tf1, Const(1.0),
        )
    if settings.tf == 0.0 or settings.kf == 0.0:
        stabilizing_feedback: Expr = Const(0.0)
    else:
        feedback_washout_state: Var = builder.lag(
            'FeedbackWashoutPu', feedback_signal, tf, settings.tf, Const(1.0),
        )
        stabilizing_feedback = kf / tf * (feedback_signal - feedback_washout_state)
    regulator_signal: Expr = voltage_error - stabilizing_feedback
    if settings.tb == 0.0:
        compensated_signal: Expr = regulator_signal
    else:
        compensated_signal = builder.lead_lag(
            'VoltageCompensatorPu', regulator_signal, tc, tb, settings.tc, settings.tb,
            regulator_signal,
        )
    if settings.vtlim:
        regulator_lower: Expr = terminal_voltage * vrmin
        regulator_upper: Expr = terminal_voltage * vrmax
    else:
        regulator_lower = vrmin
        regulator_upper = vrmax
    regulator_output: Var = builder.lag(
        'RegulatorOutputPu', ka * compensated_signal, ta, settings.ta, Const(0.0),
        regulator_lower, regulator_upper,
    )

    saturation_b: float = math.log(settings.seefd2 / settings.seefd1) / (settings.efd2 - settings.efd1)
    saturation_a: float = settings.seefd1 * math.exp(-saturation_b * settings.efd1)
    saturation: Expr = Const(saturation_a) * sym.exp(Const(saturation_b) * exciter_state)
    exciter_derivative: Expr = (regulator_output - (ke + saturation) * exciter_state) / te
    builder.block.state_vars.append(exciter_state)
    builder.block.diff_vars.append(vfactory.add_diff_var(name=f'd_{exciter_state.name}', base_var=exciter_state))
    if settings.exclim:
        lower_stop: Expr = Const(1.0) - sym.heaviside(exciter_state)
        outward_motion: Expr = sym.heaviside(-exciter_derivative)
        exciter_derivative = exciter_derivative * (Const(1.0) - lower_stop * outward_motion)
    else:
        pass
    builder.block.state_eqs.append(exciter_derivative)
    builder.block.init_eqs[exciter_state] = Const(1.0)

    if settings.ks == 0.0:
        speed_multiplier: Expr = Const(1.0)
    else:
        machine_speed: Var = builder.input('OmegaPu', Const(1.0))
        speed_multiplier = Const(1.0) + ks * (machine_speed - Const(1.0))
    field_voltage: Var = builder.algebraic(
        'EfdPu', speed_multiplier * exciter_state, exciter_state,
    )
    return builder.finish((field_voltage,), 'CGMES ExcDC2A direct-current commutator exciter')
