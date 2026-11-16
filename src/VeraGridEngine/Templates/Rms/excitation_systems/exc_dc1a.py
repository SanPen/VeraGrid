# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the License was not distributed with this
# file, You can obtain one at https://www.mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Equation-backed CGMES ExcDC1A direct-current commutator exciter."""

import math

from VeraGridEngine.Devices.Dynamic.rms_template import RmsModelTemplate
from VeraGridEngine.Devices.Dynamic.var_factory import VarFactory
from VeraGridEngine.Templates.Rms.common.control_realization import ControlRealization
from VeraGridEngine.Utils.Symbolic.symbolic import Const, Expr, Var
import VeraGridEngine.Utils.Symbolic.symbolic as sym


class ExcDC1AParameters:
    """Settings declared by the canonical CGMES ExcDC1A class."""

    __slots__ = (
        'ka', 'ks', 'ta', 'tb', 'tc', 'vrmax', 'vrmin', 'ke', 'te', 'kf', 'tf',
        'efd1', 'seefd1', 'efd2', 'seefd2', 'exclim', 'efdmin', 'efdmax',
    )

    def __init__(
            self,
            ka: float = 46.0,
            ks: float = 0.0,
            ta: float = 0.06,
            tb: float = 0.0,
            tc: float = 0.0,
            vrmax: float = 1.0,
            vrmin: float = -0.9,
            ke: float = 0.0,
            te: float = 0.46,
            kf: float = 0.1,
            tf: float = 1.0,
            efd1: float = 3.1,
            seefd1: float = 0.33,
            efd2: float = 2.3,
            seefd2: float = 0.33,
            exclim: bool = True,
            efdmin: float = -99.0,
            efdmax: float = 99.0,
    ) -> None:
        """Store canonical settings with the local EA typical values.

        :param ka: Voltage-regulator gain.
        :param ks: Speed-deviation multiplier coefficient.
        :param ta: Regulator amplifier time constant.
        :param tb: Lead-lag denominator time constant.
        :param tc: Lead-lag numerator time constant.
        :param vrmax: Regulator upper limit.
        :param vrmin: Regulator lower limit.
        :param ke: Exciter field constant.
        :param te: Exciter integration time constant.
        :param kf: Stabilizing feedback gain.
        :param tf: Stabilizing feedback time constant.
        :param efd1: First saturation voltage point.
        :param seefd1: Saturation at ``efd1``.
        :param efd2: Second saturation voltage point.
        :param seefd2: Saturation at ``efd2``.
        :param exclim: Apply a zero lower stop to the exciter integrator.
        :param efdmin: Final field-voltage lower limit.
        :param efdmax: Final field-voltage upper limit.
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
        self.efd1: float = efd1
        self.seefd1: float = seefd1
        self.efd2: float = efd2
        self.seefd2: float = seefd2
        self.exclim: bool = exclim
        self.efdmin: float = efdmin
        self.efdmax: float = efdmax


def build_exc_d_c1_a_template(
        vfactory: VarFactory,
        name: str | None = None,
        parameters: ExcDC1AParameters | None = None,
) -> RmsModelTemplate:
    """Build the DC1A regulator, washout, saturated exciter, and speed path.

    :param vfactory: Factory owning the symbolic graph.
    :param name: Optional runtime model name.
    :param parameters: Parsed canonical CGMES settings.
    :return: Equation-backed DC1A with voltage, reference, Vs, optional speed, and Efd ports.
    :raises ValueError: Invalid times, limits, or saturation points.
    """
    settings: ExcDC1AParameters = ExcDC1AParameters() if parameters is None else parameters
    template_name: str = 'ExcDC1A' if name is None else name
    numeric_values: tuple[float, ...] = (
        settings.ka, settings.ks, settings.ta, settings.tb, settings.tc,
        settings.vrmax, settings.vrmin, settings.ke, settings.te, settings.kf,
        settings.tf, settings.efd1, settings.seefd1, settings.efd2, settings.seefd2,
        settings.efdmin, settings.efdmax,
    )
    if not all(math.isfinite(value) for value in numeric_values):
        raise ValueError('ExcDC1A parameters must be finite')
    elif min(settings.ta, settings.tb, settings.tc, settings.tf) < 0.0 or settings.te <= 0.0:
        raise ValueError('ExcDC1A times must be nonnegative and TE positive')
    elif settings.tb == 0.0 and settings.tc != 0.0:
        raise ValueError('ExcDC1A zero TB requires zero TC')
    elif settings.vrmin >= settings.vrmax or settings.efdmin >= settings.efdmax:
        raise ValueError('ExcDC1A regulator and field limits must be ordered')
    elif settings.efd1 <= 0.0 or settings.efd2 <= 0.0 or settings.efd1 == settings.efd2:
        raise ValueError('ExcDC1A saturation voltages must be distinct and positive')
    elif settings.seefd1 <= 0.0 or settings.seefd2 <= 0.0:
        raise ValueError('ExcDC1A saturation values must be positive')
    elif settings.tf == 0.0 and settings.kf != 0.0:
        raise ValueError('ExcDC1A TF must be positive when KF is nonzero')
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
    efd1: Var = builder.parameter('EFD1', settings.efd1)
    seefd1: Var = builder.parameter('SEefd1', settings.seefd1)
    efd2: Var = builder.parameter('EFD2', settings.efd2)
    seefd2: Var = builder.parameter('SEefd2', settings.seefd2)
    efdmin: Var = builder.parameter('EFDMIN', settings.efdmin)
    efdmax: Var = builder.parameter('EFDMAX', settings.efdmax)
    terminal_voltage: Var = builder.input('UsPu', Const(1.0))
    reference: Var = builder.input('UsRefPu', Const(1.0))
    supplementary: Var = builder.input('UpssPu', Const(0.0))
    voltage_error: Expr = reference - terminal_voltage + supplementary
    exciter_state: Var = vfactory.add_var(f'ExciterVoltagePu_{template_name}')

    if settings.tb == 0.0:
        compensated_error: Expr = voltage_error
    else:
        compensated_error = builder.lead_lag(
            'VoltageCompensatorPu', voltage_error, tc, tb, settings.tc, settings.tb,
            voltage_error,
        )
    if settings.tf == 0.0 or settings.kf == 0.0:
        stabilizing_feedback: Expr = Const(0.0)
    else:
        feedback_state: Var = builder.lag(
            'FeedbackFilterPu', exciter_state, tf, settings.tf, Const(1.0),
        )
        stabilizing_feedback = kf / tf * (exciter_state - feedback_state)
    regulator_input: Expr = compensated_error - stabilizing_feedback
    regulator_output: Var = builder.lag(
        'RegulatorOutputPu', ka * regulator_input, ta, settings.ta, Const(0.0),
        vrmin, vrmax,
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
        'EfdPu', sym.hard_sat(speed_multiplier * exciter_state, efdmin, efdmax),
        Const(1.0),
    )
    return builder.finish((field_voltage,), 'CGMES ExcDC1A direct-current commutator exciter')
